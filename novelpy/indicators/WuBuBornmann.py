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
                variable = None,
                client_name = None,
                db_name = None,
                list_ids = None):
        """
        
        Description
        -----------
        Compute several indicators of disruptiveness studied in Bornmann and Tekles (2020)

        Parameters
        ----------
        collection_name: str
            Name of the collection or the json file containing the variables. 
        focal_year : int
            year of interest
        id_variable : str
            id variable name.
        refs_list_variable : str
            Name of the key which value is a List of IDs cited by the focal paper.
        cits_list_variable : str
            Name of the key which value is a List of IDs that cite focal paper
        focal_year: int
            Calculate the novelty score for every document which has a year_variable = focal_year.
        id_variable: str
            Name of the key which value give the identity of the document.
        year_variable : str
            Name of the key which value is the year of creation of the document.
        client_name: str
            Mongo URI if your data is hosted on a MongoDB instead of a JSON file.
        db_name: str 
            Name of the MongoDB.

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
        self.list_ids = list_ids
        if variable == None:
            self.variable = "citations"
        else:
            self.variable = variable

        create_output.__init__(
            self,
            client_name = client_name,
            db_name = db_name,
            collection_name = collection_name,
            id_variable = id_variable,
            year_variable = year_variable,
            variable = self.variable,
            focal_year = focal_year,
            list_ids = list_ids)

        if client_name:
            self.tomongo = True
            if "output_disruptiveness" not in self.db.list_collection_names():
                print("Init output collection with index on id_variable ...")
                self.collection_output = self.db["output_disruptiveness"]
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
        if self.tomongo:
            docs = self.collection.find({self.year_variable:self.focal_year})
            if self.list_ids:
                self.papers_items = {doc[self.id_variable]:doc[self.variable] for doc in docs if doc[self.id_variable] in self.list_ids}
            else:
                self.papers_items = {doc[self.id_variable]:doc[self.variable] for doc in docs}
        else:
            self.citation_network = pickle.load(open('Data/docs/{}.pkl'.format(self.collection_name),'rb'))
            self.papers_items = {pmid:self.citation_network[pmid] for pmid in self.citation_network if self.citation_network[pmid][self.year_variable] == self.focal_year}

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
            focal_paper_id = focal_paper_id
            
            # papers that cites our focal paper
            
            citing_focal_paper = dict()
            ids = set()
            for citer in focal_paper_cits:
                doc = collection.find_one({self.id_variable:citer})
                if doc:
                    if self.variable in doc:
                        citing_focal_paper.update({doc[self.id_variable]: doc[self.variable][self.refs_list_variable]})
                        ids.update([citer])

            
            # papers that cite refs from focal paper

            citing_ref_from_focal_paper = dict()
            ids = set()
            for ref in focal_paper_refs:
                doc = collection.find_one({self.id_variable:ref})
                if doc:
                    if self.variable in doc:
                        for citing_paper in doc[self.variable][self.cits_list_variable]:
                             if all([citing_paper != focal_paper_id,
                                citing_paper not in ids,
                                doc[self.year_variable] >= self.focal_year]):

                                ref_citers = collection.find_one({self.id_variable:citing_paper})
                                if ref_citers:
                                    if self.variable in ref_citers.keys():
                                        if ref_citers[self.id_variable] != focal_paper_id:
                                            citing_ref_from_focal_paper.update({
                                                ref_citers[self.id_variable]: ref_citers[self.variable][self.refs_list_variable]
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
                    citing_focal_paper.update({citer: doc[self.variable][self.refs_list_variable]})
                    ids.update([citer])
            
            # papers that cite refs from focal paper
            citing_ref_from_focal_paper = dict()
            ids = set()
            for ref in focal_paper_refs:
                try:
                    citing_ref_from_fp = self.citation_network[ref][self.variable][self.cits_list_variable]
                    for citing_paper in citing_ref_from_fp :

                        if all([citing_paper != focal_paper_id,
                                citing_paper not in ids]):
                            citing_paper_doc = self.citation_network[citing_paper]
                            if citing_paper_doc['year'] >= self.focal_year:
                                citers_refs = self.citation_network[citing_paper][self.variable][self.refs_list_variable]
                                citing_ref_from_focal_paper.update({citing_paper: citers_refs})
                                ids.update([citing_paper])
                except Exception as e:
                    print(e)

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
                },
            "year":self.focal_year
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
                    'disruptiveness':disruptiveness_indicators['disruptiveness'],
                    "year":self.focal_year}

    def get_indicators(self,parallel = False):
        

        def compute_scores_par(focal_paper_id, 
                           focal_paper_refs,
                           focal_paper_cits,
                           tomongo,
                           focal_year,
                           refs_list_variable,
                           cits_list_variable,
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

            client = pymongo.MongoClient(kwargs['client_name'])
            db = client[kwargs['db_name']]
            collection = db[kwargs['collection_name']]
            focal_paper_id = focal_paper_id
            
            # papers that cites our focal paper
            
            citing_focal_paper = dict()
            ids = set()
            for citer in focal_paper_cits:
                doc = collection.find_one({id_variable:citer})
                if self.variable in doc:
                    citing_focal_paper.update({doc[id_variable]: doc[self.variable][refs_list_variable]})
                    ids.update([citer])
            
            
            # papers that cite refs from focal paper

            citing_ref_from_focal_paper = dict()
            ids = set()
            for ref in focal_paper_refs:
                doc = collection.find_one({id_variable:ref})
                if self.variable in doc.keys():
                    for citing_paper in doc[self.variable][cits_list_variable]:
                         if all([citing_paper != focal_paper_id,
                            citing_paper not in ids,
                            doc['year'] >= focal_year]):
                                 
                            ref_citers = collection.find_one({id_variable:citing_paper})
                            if self.variable in ref_citers.keys():
                                if ref_citers[id_variable] != focal_paper_id:
                                    citing_ref_from_focal_paper.update({
                                        ref_citers[id_variable]: ref_citers[self.variable][refs_list_variable]
                                    })
                                    ids.update([ref_citers[id_variable]])

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
                    client.close()
                except Exception as e:
                    print(e)
            else:
                return {id_variable:focal_paper_id,
                        'disruptiveness':disruptiveness_indicators['disruptiveness']} 

    
        print("Load citation network ...")  
        self.get_citation_network()   

        print('Getting score per paper ...')  
        if parallel:
            if self.tomongo:
                #Parallel(n_jobs=10)(delayed(compute_scores_par)(
                for idx in tqdm.tqdm(list(self.papers_items)):
                            compute_scores_par(
                                focal_paper_id = idx,
                                focal_paper_refs = self.papers_items[idx][self.refs_list_variable],
                                focal_paper_cits = self.papers_items[idx][self.cits_list_variable],
                                tomongo = self.tomongo,
                                focal_year = self.focal_year,
                                refs_list_variable = self.refs_list_variable,
                                cits_list_variable = self.cits_list_variable,
                                id_variable = self.id_variable,
                                year_variable = self.year_variable,
                                client_name = self.client_name, 
                                db_name = self.db_name,
                                collection_name = self.collection_name,
                                collection2update = 'output_disruptiveness')
                #for idx in tqdm.tqdm(list(self.papers_items)))
            else:
                print('Parallel computing only available with mongoDB')
        else:    
            list_of_insertion = []
            for idx in tqdm.tqdm(list(self.papers_items)):
                if self.tomongo:
                    focal_paper_refs = self.papers_items[idx][self.refs_list_variable]
                    focal_paper_cits = self.papers_items[idx][self.cits_list_variable]
                else:
                    focal_paper_refs = self.papers_items[idx][self.variable][self.refs_list_variable]
                    focal_paper_cits = self.papers_items[idx][self.variable][self.cits_list_variable]

                paper_score = self.compute_scores(
                    focal_paper_id = idx,
                    focal_paper_refs = focal_paper_refs,
                    focal_paper_cits = focal_paper_cits,
                    client_name = self.client_name, 
                    db_name = self.db_name,
                    collection_name = self.collection_name,
                    collection2update = 'output_disruptiveness')
                list_of_insertion.append(paper_score)
            if not self.tomongo:
                with open(self.path_output + "/{}.json".format(self.focal_year), 'w') as outfile:
                    json.dump(list_of_insertion, outfile)
        print("Done !")     
        
        