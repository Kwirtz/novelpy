import pymongo
import numpy as np 
import pandas as pd
# import dask.dataframe as dd

class Disruptiveness:

    def __init__(self,
                focal_year,
                var_id,
                var_refs_list,
                var_year):
        """
        
        Description
        -----------
        Compute several indicators of disruptiveness studied in Bornmann and Tekles (2020)

        Parameters
        ----------
        focal_year : int
            year of interest
        var_id : str
            id variable name.
        var_refs_list : str
            cited references list variable name .
        var_year : str
            year variable name

        Returns
        -------
        None.

        """
        
        self.focal_year = focal_year
        self.var_id = var_id 
        self.var_refs_list = var_refs_list
        self.var_year = var_year

    def get_citation_network(self,path2citnet):
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
        citation_network = pd.read_json(path2citnet,
                                        dtype={self.var_id:'uint32',
                                               self.var_refs_list:'uint32',
                                               self.var_year:'uint16'})
        # citation_network = dd.from_pandas(citation_network,npartitions = 8)                                                        
        citation_network = citation_network.dropna(subset=[self.var_refs_list])
        citation_network = citation_network[citation_network[self.var_year] != '']\
            .astype({self.var_year:'uint32'})
        # Restrict to pmids that are published from one year before the focal_year to present
        # (a cited paper pmid may be finaly published in a journal a bit later than the citing paper)
        citation_network = citation_network[citation_network[self.var_year]>=(self.focal_year-1)]
        citation_network = citation_network.explode(self.var_refs_list)
        # citation_network = citation_network.compute()
        # citation_network =  dd.from_pandas(citation_network,npartitions = 8)
        self.citation_network = citation_network.set_index([self.var_id,self.var_refs_list])
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
            
            docs =[doc for doc in collection.find({self.var_refs_list:focal_paper_id})]
            citing_focal_paper = pd.DataFrame(docs)
            
            docs =[doc for doc in collection.find({self.var_refs_list:{'$in':focal_paper_refs},
                                                   self.var_id:{'$ne':focal_paper_id},
                                                   self.var_year:{'$gt':(self.focal_year-1)}})]
            
            citing_ref_from_focal_paper = pd.DataFrame(docs)
    
        else:
            idx = self.citation_network.index.get_level_values(self.var_refs_list) == focal_paper_id
            citing_focal_paper_pmid = list(self.citation_network[idx].reset_index()[self.var_id])
        
            idx = self.citation_network.index.isin(citing_focal_paper_pmid, level=self.var_id)
            citing_focal_paper = self.citation_network[idx]\
                .reset_index()\
                .groupby(self.var_id)[self.var_refs_list]\
                .apply(list)\
                .reset_index()
            
            idx = self.citation_network.index.isin(focal_paper_refs, level=self.var_refs_list)
            citing_ref_from_focal_paper = self.citation_network[idx].reset_index()
            
            idx = citing_ref_from_focal_paper.PMID != focal_paper_id
            citing_ref_from_focal_paper = citing_ref_from_focal_paper[idx]
            citing_ref_from_focal_paper = citing_ref_from_focal_paper\
                .reset_index()\
                .groupby(self.var_id)[self.var_refs_list]\
                .apply(list)\
                .reset_index()
        
        citing_focal_paper = {
            row[self.var_id]:row[self.var_refs_list] for index, row in citing_focal_paper.iterrows()
            }

        citing_ref_from_focal_paper = {
            row[self.var_id]:row[self.var_refs_list] for index, row in citing_ref_from_focal_paper.iterrows()
            }
   
        J = set(citing_focal_paper.keys()).intersection(citing_ref_from_focal_paper.keys())
        I = np.setdiff1d(set(citing_focal_paper.keys()),J)
        K = np.setdiff1d(set(citing_ref_from_focal_paper.keys()),J)

        Jxc = [len(set(focal_paper_refs).intersection(cited_ref)) for cited_ref in citing_focal_paper.values()]
        
        J5 = [len_match_ref for len_match_ref in Jxc if len_match_ref > 4]
        
        Breadth = [pmid for pmid in citing_focal_paper
                   if not any([ref in citing_focal_paper.keys() for ref in citing_focal_paper[pmid]])]
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
                query = { self.var_id: focal_paper_id}
                newvalue =  { '$set': disruptiveness_indicators}
                db[kwargs['collection2update']].update_one(query,newvalue)
            except Exception as e:
                print(e)
        else:
            return {focal_paper_id:disruptiveness_indicators}