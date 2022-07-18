import pymongo
import numpy as np 
import pandas as pd
from novelpy.utils.run_indicator_tools import create_output
import tqdm
import os
import glob
# import dask.dataframe as dd
from joblib import Parallel, delayed
import pickle
import json

class Disruptiveness(create_output):

    def __init__(self,
                collection_name,
                focal_year,
                id_variable,
                refs_list_variable,
                cits_list_variable,
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
        self.cits_list_variable = cits_list_variable
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
            variable = 'citations',
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
        self.citation_network = pickle.load(open('Data/docs/Citation_network.pkl','rb'))


    def compute_scores(self,
                       focal_paper_id, 
                       focal_paper_refs,
                       focal_paper_cits,
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
  
        if self.tomongo:
            client = pymongo.MongoClient(kwargs['client_name'])
            db = client[kwargs['db_name']]
            collection = db[kwargs['collection_name']]
            focal_paper_id = int(focal_paper_id)
            
            # papers that cites our focal paper
            
            citing_focal_paper = dict()
            ids = set()
            for citer in focal_paper_cits:
                doc = collection.find_one({self.id_variable:citer})
                if 'citations' in doc:
                    citing_focal_paper.update({doc[self.id_variable]: doc['citations'][self.refs_list_variable]})
                    ids.update([citer])
            
            
            # papers that cite refs from focal paper

            citing_ref_from_focal_paper = dict()
            ids = set()
            for ref in focal_paper_refs:
                doc = collection.find_one({self.id_variable:ref})
                if 'citations' in doc.keys():
                    for citing_paper in doc['citations'][self.cits_list_variable]:
                         if all([citing_paper != focal_paper_id,
                            citing_paper not in ids,
                            doc['year'] >= self.focal_year]):
                                 
                            ref_citers = collection.find_one({self.id_variable:citing_paper})
                            if 'citations' in ref_citers.keys():
                                if ref_citers[self.id_variable] != focal_paper_id:
                                    citing_ref_from_focal_paper.update({
                                        ref_citers[self.id_variable]: ref_citers['citations'][self.refs_list_variable]
                                    })
                                    ids.update([ref_citers[self.id_variable]])

            
        else:
            
            # papers that cites our focal paper
            citing_focal_paper = dict()
            ids = set()
            for citer in focal_paper_cits:
                #try:
                if citer not in ids:
                    doc = self.citation_network[citer]
                    citing_focal_paper.update({citer: doc['citations'][self.refs_list_variable]})
                    ids.update([citer])
            
            # papers that cite refs from focal paper
            citing_ref_from_focal_paper = dict()
            ids = set()
            for ref in focal_paper_refs:
                citing_ref_from_fp = self.citation_network[ref]['citations'][self.cits_list_variable]
                for citing_paper in citing_ref_from_fp :

                    if all([citing_paper != focal_paper_id,
                            citing_paper not in ids,
                            citing_paper_doc['year'] >= self.focal_year]):
                        citing_paper_doc = self.citation_network[citing_paper]
                        citers_refs = self.citation_network[citing_paper]['citations'][self.refs_list_variable]
                        citing_ref_from_focal_paper.update({citing_paper: citers_refs})
                        ids.update([citing_paper])


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
        
        if self.tomongo:
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
        

        def compute_scores_par(focal_paper_id, 
                           focal_paper_refs,
                           focal_paper_cits,
                           tomongo,
                           focal_year,
                           refs_list_variable,
                           id_variable,
                           year_variable,
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

                # papers that cites our focal paper
                #docs = [collection.find_one({self.id_variable:citer})[0] for citer in focal_paper_cits]

                docs =[doc for doc in collection.find({refs_list_variable:focal_paper_id})]
                citing_focal_paper = pd.DataFrame(docs)

                # papers that cite refs from focal paper

                #docs = [collection.find_one({self.id_variable:ref})[0] for ref in focal_paper_refs]
                #docs = [doc for doc in docs if doc[self.id_variable] != focal_paper_id]
                docs =[doc for doc in collection.find({refs_list_variable:{'$in':focal_paper_refs},
                                                       id_variable:{'$ne':focal_paper_id},
                                                       year_variable:{'$gt':(focal_year-1)}})]

                citing_ref_from_focal_paper = pd.DataFrame(docs)


            citing_focal_paper = {
                row[id_variable]:row[refs_list_variable] for index, row in citing_focal_paper.iterrows()
                }

            citing_ref_from_focal_paper = {
                row[id_variable]:row[refs_list_variable] for index, row in citing_ref_from_focal_paper.iterrows()
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
                    query = { id_variable: focal_paper_id}
                    newvalue =  { '$set': disruptiveness_indicators}
                    db[kwargs['collection2update']].update_one(query,newvalue,upsert = True)
                except Exception as e:
                    print(e)
            else:
                return {id_variable:focal_paper_id,
                        'disruptiveness':disruptiveness_indicators['disruptiveness']} 

        
        if not self.tomongo:
            print("Load citation network ...")  
            self.get_citation_network()   
            self.papers_items = {pmid:self.citation_network[pmid] for pmid in self.citation_network if self.citation_network[pmid][self.year_variable] == self.focal_year}
        else:
            self.get_item_paper()
        print('Getting score per paper ...')  
        if parallel:
            if self.tomongo:
                Parallel(n_jobs=10)(delayed(compute_scores_par)(
                            focal_paper_id = idx,
                            focal_paper_refs = self.papers_items[idx],#['citations'][self.refs_list_variable],
                            focal_paper_cits = self.papers_items[idx],#['citations'][self.cits_list_variable],
                            tomongo = self.tomongo,
                            focal_year = self.focal_year,
                            refs_list_variable = self.refs_list_variable,
                            id_variable = self.id_variable,
                            year_variable = self.year_variable,
                            client_name = self.client_name, 
                            db_name = self.db_name,
                            collection_name = self.collection_name,
                            collection2update = 'output')
                for idx in tqdm.tqdm(list(self.papers_items)))
            else:
                print('Parallel computing only available with mongoDB')
        else:    
            list_of_insertion = []
            for idx in tqdm.tqdm(list(self.papers_items)):
                if self.tomongo:
                    focal_paper_refs = self.papers_items[idx][self.refs_list_variable]
                    focal_paper_cits = self.papers_items[idx][self.cits_list_variable]
                else:
                    focal_paper_refs = self.papers_items[idx]['citations'][self.refs_list_variable]
                    focal_paper_cits = self.papers_items[idx]['citations'][self.cits_list_variable]

                paper_score = self.compute_scores(
                    focal_paper_id = idx,
                    focal_paper_refs = focal_paper_refs,
                    focal_paper_cits = focal_paper_cits,
                    client_name = self.client_name, 
                    db_name = self.db_name,
                    collection_name = self.collection_name,
                    collection2update = 'output')
                list_of_insertion.append(paper_score)
            if not self.tomongo:
                with open(self.path_output + "/{}.json".format(self.focal_year), 'w') as outfile:
                    json.dump(list_of_insertion, outfile)
        print("Done !")     
        
        