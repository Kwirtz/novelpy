import pymongo
import numpy as np 
import pandas as pd
from novelpy.utils.run_indicator_tools import create_output
import tqdm
import os
import glob
# import dask.dataframe as dd

class Disruptiveness(create_output):

    def __init__(self,
                collection_name,
                focal_year,
                id_variable,
                refs_list_variable,
                year_variable,
                client_name = None,
                db_name = None):
        """
        
        Description
        -----------
        Compute several indicators of disruptiveness studied in Bornmann and Tekles (2020)

        Parameters
        ----------
        focal_year : int
            year of interest
        id_variable : str
            id variable name.
        refs_list_variable : str
            cited references list variable name .
        year_variable : str
            year variable name

        Returns
        -------
        None.

        """
        self.indicator = 'disruptiveness'
        self.focal_year = focal_year
        self.id_variable = id_variable 
        self.refs_list_variable = refs_list_variable
        self.year_variable = year_variable
        self.client_name = client_name
        self.db_name = db_name
        self.collection_name = collection_name


        create_output.__init__(
            self,
            client_name = client_name,
            db_name = db_name,
            collection_name = collection_name,
            id_variable = id_variable,
            year_variable = year_variable,
            variable = refs_list_variable,
            focal_year = focal_year)

        if client_name:
            self.tomongo = True
            if "output" not in self.db.list_collection_names():
                print("Init output collection with index on id_variable ...")
                self.collection_output = self.db["output"]
                self.collection_output.create_index([ (self.id_variable,1) ])
        else:
            self.tomongo = False
            self.path_output = "Result/Disruptiveness"
            if not os.path.exists(self.path_output):
                        os.makedirs(self.path_output)

    def get_citation_network(self):
        """
        
        Description
        -----------
        Read a json, remove data before focal year and explode lists of cited references 
        Use only when not using mongo
    
        Parameters
        ----------
        path2citnet : str
            path to json file.
            
        Returns
        -------
        pandas.core.frame.DataFrame
            Citation network indexed by pmid and cited reference.

        """
        files = glob.glob(r'Data\docs\Citation_net_sample\*.json')
        citation_network = pd.DataFrame()
        for file in files:
            temp = pd.read_json(file,
                                dtype={self.id_variable:'uint32',
                                       self.refs_list_variable:'uint32',
                                       self.year_variable:'uint16'})
            citation_network = pd.concat([citation_network,temp])

        # citation_network = dd.from_pandas(citation_network,npartitions = 8)                                                        
        citation_network = citation_network.dropna(subset=[self.refs_list_variable])
        citation_network = citation_network[citation_network[self.year_variable] != '']\
            .astype({self.year_variable:'uint32'})
        # Restrict to pmids that are published from one year before the focal_year to present
        # (a cited paper pmid may be finaly published in a journal a bit later than the citing paper)
        citation_network = citation_network[citation_network[self.year_variable]>=(self.focal_year-1)]
        citation_network = citation_network.explode(self.refs_list_variable)
        # citation_network = citation_network.compute()
        # citation_network =  dd.from_pandas(citation_network,npartitions = 8)
        self.citation_network = citation_network.set_index([self.id_variable,self.refs_list_variable])
        return self.citation_network

    def compute_scores(self,
                       focal_paper_id, 
                       focal_paper_refs,
                       tomongo,
                       **kwargs):
        """

        Description
        -----------

        Parameters
        ----------
        focal_paper_id : int
            id of the document treated.
        focal_paper_refs : list
            list of id (int) of cited references.
        tomongo : bool
            query and update data with mongodb.
        **kwargs : keyword arguments for mongo
            client_name : client name
            db_name : db name 
            collection_name : collection name from which citation network querying
            collection2update : collection name to update with indicators
        Returns
        -------
        dict
            several indicators of disruptiveness 

        """
  
        if tomongo:
            client = pymongo.MongoClient(kwargs['client_name'])
            db = client[kwargs['db_name']]
            collection = db[kwargs['collection_name']]
            focal_paper_id = int(focal_paper_id)
            
            docs =[doc for doc in collection.find({self.refs_list_variable:focal_paper_id})]
            citing_focal_paper = pd.DataFrame(docs)
            
            docs =[doc for doc in collection.find({self.refs_list_variable:{'$in':focal_paper_refs},
                                                   self.id_variable:{'$ne':focal_paper_id},
                                                   self.year_variable:{'$gt':(self.focal_year-1)}})]
            
            citing_ref_from_focal_paper = pd.DataFrame(docs)
    
        else:
            idx = self.citation_network.index.get_level_values(self.refs_list_variable) == focal_paper_id
            citing_focal_paper_pmid = list(self.citation_network[idx].reset_index()[self.id_variable])
        
            idx = self.citation_network.index.isin(citing_focal_paper_pmid, level=self.id_variable)
            citing_focal_paper = self.citation_network[idx]\
                .reset_index()\
                .groupby(self.id_variable)[self.refs_list_variable]\
                .apply(list)\
                .reset_index()
            
            idx = self.citation_network.index.isin(focal_paper_refs, level=self.refs_list_variable)
            citing_ref_from_focal_paper = self.citation_network[idx].reset_index()
            
            idx = citing_ref_from_focal_paper.PMID != focal_paper_id
            citing_ref_from_focal_paper = citing_ref_from_focal_paper[idx]
            citing_ref_from_focal_paper = citing_ref_from_focal_paper\
                .reset_index()\
                .groupby(self.id_variable)[self.refs_list_variable]\
                .apply(list)\
                .reset_index()
        
        
        citing_focal_paper = {
            row[self.id_variable]:row[self.refs_list_variable] for index, row in citing_focal_paper.iterrows()
            }

        citing_ref_from_focal_paper = {
            row[self.id_variable]:row[self.refs_list_variable] for index, row in citing_ref_from_focal_paper.iterrows()
            }
        # papers that cite the focal paper that also cite reference from the focal paper
        J = set(citing_focal_paper.keys()).intersection(citing_ref_from_focal_paper.keys())
        
        # papers that cite the focal paper but do not cite reference from the focal paper
        I = set(citing_focal_paper.keys()) - J
        
        # papers that do not cite the focal paper but cite reference from the focal paper
        K = set(citing_ref_from_focal_paper.keys()) - J

        # number of reference cited by a paper that cite the focal paper that are cited by the focal paper
        Jxc = [len(set(focal_paper_refs).intersection(cited_ref)) for cited_ref in citing_focal_paper.values()]
        
        # keep papers that cite the focal paper that share at least 5 references with the focal paper
        J5 = [len_match_ref for len_match_ref in Jxc if len_match_ref > 4]
        
        # papers that cite the focal paper that do not cite papers that cite the focal paper
        Breadth = [pmid for pmid in citing_focal_paper
                   if not any([ref in citing_focal_paper.keys() for ref in citing_focal_paper[pmid]])]
        
        # papers that cite the focal paper that cite at least one other paper that cite the focal paper
        Depth = [pmid for pmid in citing_focal_paper
                   if any([ref in citing_focal_paper.keys() for ref in citing_focal_paper[pmid]])]
        
        len_I = len(I) if I else 0
        len_J = len(J) if J else 0
        len_J5 = len(J5) if J5 else 0
        len_K = len(K) if K else 0
        sum_Jxc = sum(Jxc) if Jxc else 0
        len_B = len(Breadth) if Breadth else 0
        len_D = len(Depth) if Depth else 0
        
        disruptiveness_indicators = {
            'disruptiveness' : {
                'DI1': (len_I-len_J)/(len_I+len_J+len_K) if any([len_I,len_J,len_K !=0]) else 0,
                'DI5': (len_I-len_J5)/(len_I+len_J5+len_K)if any([len_I,len_J5,len_K !=0]) else 0,
                'DI5nok': (len_I-len_J5)/(len_I+len_J5) if any([len_I,len_J5 !=0]) else 0,
                'DI1nok': (len_I-len_J)/(len_I+len_J) if any([len_I,len_J !=0]) else 0,
                'DeIn': sum_Jxc/(len_I+len_J) if any([len_I,len_J !=0]) else 0,
                'Breadth' : len_B/(len_I+len_J) if any([len_I,len_J !=0]) else 0,
                'Depth' : len_D/(len_I+len_J) if any([len_I,len_J !=0]) else 0
                }
            }
        
        if tomongo:
            try:
                query = { self.id_variable: focal_paper_id}
                newvalue =  { '$set': disruptiveness_indicators}
                db[kwargs['collection2update']].update_one(query,newvalue,upsert = True)
            except Exception as e:
                print(e)
        else:
            return {self.id_variable:focal_paper_id,
                    'disruptiveness':disruptiveness_indicators['disruptiveness']}

    def get_indicators(self,parallel = False):
        self.get_item_paper()
        if not self.tomongo:
            print("Load citation network ...")  
            self.get_citation_network()
            print("Citation network loaded !")     

        print('Getting score per paper ...')  
        if parallel:
            Parallel(n_jobs=30)(delayed(self.compute_scores)(
                        focal_paper_id = idx,
                        focal_paper_refs = self.papers_items[idx],
                        tomongo = self.tomongo,
                        client_name = self.client_name, 
                        db_name = self.db_name,
                        collection_name = self.collection_name,
                        collection2update = 'output')
            for idx in tqdm.tqdm(list(self.papers_items)))
        else:    
            list_of_insertion = []
            for idx in tqdm.tqdm(list(self.papers_items)):
                paper_score = self.compute_scores(
                    focal_paper_id = idx,
                    focal_paper_refs = self.papers_items[idx],
                    tomongo = self.tomongo,
                    client_name = self.client_name, 
                    db_name = self.db_name,
                    collection_name = self.collection_name,
                    collection2update = 'output')
                list_of_insertion.append(paper_score)
            if not self.tomongo:
                with open(self.path_output + "/{}.json".format(self.focal_year), 'w') as outfile:
                    json.dump(list_of_insertion, outfile)
        print("Done !")     