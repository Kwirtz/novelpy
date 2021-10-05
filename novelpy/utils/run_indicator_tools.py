import numpy as np
from sklearn import preprocessing
from scipy.sparse import csr_matrix, triu, lil_matrix
from itertools import combinations
import pandas as pd
import tqdm
import pymongo
import pickle
import json
import os
import re
from multiprocessing import Process, Manager
import traceback
import sys

class Dataset:
    
    def __init__(self,
             var = None,
             var_id = None,
             var_year = None,
             focal_year = None,
             indicator = None,
             sub_var = None,
             tw_cooc = None,
             client_name = None,
             db_name = None,
             collection_name = None):
        """
        Description
        -----------
        Class that returns items list for each paper and the adjacency matrix for the focal year.
        Also returns item info depending of indicator.
        
        Parameters
        ----------
        
        var : str
            variable of interest.
        var_id : str
            id variable name. 
        var_year : str
            year variable name.
        focal_year : int
            year of interest.
        sub_var : str, optional
            subvariable of interest. The default is None.
        client_name : str, optional
            client name. The default is None.
        db_name : str, optional
            db name. The default is None.
        collection_name : str, optional
            collection name. The default is None.
    
        Returns
        -------
        None.
    
        """
        self.VAR = var
        self.VAR_ID = var_id
        self.VAR_YEAR = var_year
        self.SUB_VAR = sub_var
        self.focal_year = focal_year
        self.indicator = indicator
        self.tw_cooc = tw_cooc
        self.client_name = client_name
        self.db_name = db_name
        self.collection_name = collection_name
        self.item_name = self.VAR.split('_')[0] if self.VAR else None
        
        if self.client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]

            
    def get_item_infos(self,
                       item):
        """
   
        Description
        -----------        
        Get item info depedning on the indicator

        Parameters
        ----------
        item : dict
            item from a document list of items.
        indicator : str
            indicator for which the score is computed.

        Returns
        -------
        doc_item : dict/list
            dict or list depending on the indicator structured as needed for later usage.

        """
     
        if self.indicator == 'atypicality':
            if 'year' in item.keys():
                doc_item = {'item':item[self.SUB_VAR],
                                  'year':item['year']}
        elif self.indicator == 'kscores': 
            doc_item = item
        else:
            doc_item = item[self.SUB_VAR]
        
        return  doc_item
        
    
    def get_item_paper(self):
        """
        
        Description
        -----------        
        Get items info depedning on the indicator for all documents in a given year
        
        Parameters
        ----------
        indicator : str
            indicator for which the score is computed.

        Returns
        -------
        papers_items: dict
            dict with document id and item strucutured as needed

        """
        
        # Get docs where variable of interest exists and published in focal_year
        if self.client_name:
            self.docs = self.collection.find({
                self.VAR:{'$exists':'true'},
                self.VAR_YEAR:self.focal_year
                })
        else:
            self.docs = json.load(open("Data/docs/articles/{}.json".format(self.focal_year)) )
        
        # dict of every docs. Each one contains doc_items
        self.papers_items = dict()
        
        for doc in tqdm.tqdm(self.docs):
            doc_items = list()
            for item in doc[self.VAR]:
                if self.SUB_VAR:
                    doc_item = self.get_item_infos(item)
                    if doc_item:
                        doc_items.append(doc_item)
                else:
                    if doc:
                        doc_items.append(item)
                    
            self.papers_items.update({int(doc[self.VAR_ID]):doc_items})  

    def sum_cooc_matrix(self,window):
        """
        
    
        Parameters
        ----------
        time_window : int
            time window to compute the difficulty in the past and the reutilisation in the futur.
        path : str
            path to adjacency matrices.
    
        Returns
        -------
        matrix : scipy.sparse.csr.csr_matrix
            sum of considered matrices.
    
        """
        
        i = 0
        for year in window:
            if i == 0:
                cooc = pickle.load(open( self.path + "/{}.p".format(year), "rb" ))
                i += 1
            else:
                cooc += pickle.load(open( self.path + "/{}.p".format(year), "rb" ))            
        return cooc

    def get_cooc(self):
        
        unw = ['novelty']
        type1 = 'unweighted_network' if self.indicator in unw else 'weighted_network'
        type2 = 'no_self_loop' if self.indicator in unw else 'self_loop'
        self.path = "Data/{}/{}_{}".format(self.VAR,type1,type2)
        self.name2index = pickle.load(open(self.path + "/name2index.p", "rb" ))
        if self.indicator == "foster":
            self.current_adj = self.sum_cooc_matrix( window = range(1980, self.focal_year))
        
        elif self.indicator == "novelty":
            print("Calculate past matrix ")
            self.past_adj = self.sum_cooc_matrix( window = range(1980, self.focal_year))

            print('Calculate futur matrix')
            self.futur_adj = self.sum_cooc_matrix(window = range(self.focal_year+1, self.focal_year+self.tw_cooc+1))

            print('Calculate difficulty matrix')
            self.difficulty_adj = self.sum_cooc_matrix(window = range(self.focal_year-self.tw_cooc,self.focal_year))
        else:
            self.current_adj =  pickle.load( open(self.path+'/{}.p'.format(self.focal_year), "rb" )) 
        

    def get_data(self):
        
        if self.indicator in ['atypicality','novelty','commonness',"foster"]:
            # Get the coocurence for self.focal_year
            print("loading cooc for focal year {}".format(self.focal_year))
            self.get_cooc()
            print("cooc loaded !")
            print("loading items for papers in {}".format(self.focal_year))    
            # Dict of paper, for each paper a list of item that appeared
            self.get_item_paper()
            print("items_loaded !")    


class create_output(Dataset):

    def get_paper_score(self,
                        **kwargs):
        """
    
        Description
        -----------
        Compute scores for a document and store indicators scores in a dict
    
        Parameters
        ----------
        kwargs : keyword arguments
            More argument for novelty as time_window or n_reutilisation
    
        Returns
        -------
        dict
            scores and indicators infos.
    
        """
        if self.unique_pairwise and self.keep_diag:
            combis = [(i,j) for i,j in combinations(set(self.current_items),2)]
        elif self.unique_pairwise == False and self.keep_diag == False:
            combis = [(i,j) for i,j in combinations(self.current_items,2) if i != j]
        elif self.unique_pairwise and self.keep_diag == False:
            combis = [(i,j) for i,j in combinations(set(self.current_items),2) if i != j]
        else:
            combis = [(i,j) for i,j in combinations(self.current_items,2)]
        
        comb_infos = []
        scores_array = []
        for combi in combis:
            combi = sorted( (self.name2index[combi[0]], self.name2index[combi[1]]) )
            comb_infos.append({"item1" : combi[0],
                          "item2" : combi[1],
                          "score" : int(self.comb_scores[combi[0], combi[1]]) })
            scores_array.append(int(self.comb_scores[combi[0], combi[1]]))
        self.scores_array = np.array(scores_array)
        
        doc_infos = {"combis":comb_infos}

        key = self.item_name + '_' + self.indicator
        if 'n_reutilisation' and 'time_window' in kwargs:
            key = key +'_'+str(kwargs['time_window'])+'y_'+str(kwargs['n_reutilisation'])+'reu'
        elif 'time_window' in kwargs:
            key = key +'_'+str(kwargs['time_window'])+'y'
           
        if self.indicator == 'novelty':
            score = {'novelty':sum(self.scores_array)}
            
        elif self.indicator == 'atypicality':
            score = {'conventionality': np.median(self.scores_array),
                     'novelty': np.quantile(self.scores_array,0.1)}
            
        elif self.indicator == 'commonness':
            score = {'novelty': -np.log(np.quantile(self.scores_array,0.1))}
        
        elif self.indicator == 'foster':
            score = {'novelty': float(np.mean(self.scores_array))}
        
        doc_infos.update({'score':score })
        self.key = key
        self.doc_infos = doc_infos
        return {key:doc_infos}
    
    def populate_list(self, **kwargs):
        """
        Description
        -----------
    
        Parameters
        ----------
        Returns
        -------
        Update on mongo paper scores or store it in a dict
    
        """
        
        # Load the score of pairs given by the indicator
        self.comb_scores = pickle.load(
                open(
                    'Data/{}/indicators_adj/{}/{}.p'.format(
                        self.VAR,self.indicator,self.focal_year),
                    "rb" ))       
        
        # Iterate over every docs 
        list_of_insertion = []
        for idx in tqdm.tqdm(list(self.papers_items),desc='start'):
        
            if self.indicator in ['atypicality','novelty','commonness','foster']:
                # Check that you have more than 2 item (1 combi) else no combination and no novelty 
                if len(self.papers_items[idx])>2:
                    self.current_items = self.papers_items[idx]
                    if self.indicator != 'novelty':
                        self.unique_pairwise = False
                        self.keep_diag=True
                    else:
                        self.unique_pairwise = True
                        self.keep_diag=False
                                   
                    # Use novelty score of combination + Matrix of combi of papers to have novelty score of the paper with VAR_ID = idx
                    self.get_paper_score(**kwargs)
                else:
                    continue
            
            elif 'new_infos' in kwargs:
                self.doc_infos = kwargs['new_infos']
            
            
            if self.client_name:
                list_of_insertion.append(pymongo.UpdateOne({self.VAR_ID: int(idx)},
                                                           {'$set': {self.key: self.doc_infos}},
                                                           upsert = True))
            else:
                list_of_insertion.append({self.VAR_ID: int(idx),self.key: self.doc_infos})

        
        if self.client_name:
            self.collection_output.bulk_write(list_of_insertion)
        else:
            with open(self.path_output + "/{}.json".format(self.focal_year), 'w') as outfile:
                json.dump(list_of_insertion, outfile)        
    
    def update_paper_values(self, **kwargs):
        """

        Description
        -----------        
        run database update

        Parameters
        ----------
        **kwargs : keyword arguments, optional
            More argument for novelty as time_window or n_reutilisation.
            
        Returns
        -------
        None.

        """
        if self.client_name:
            if "output" not in self.db.list_collection_names():
                print("Init output collection with index on var_id ...")
                self.collection_output = self.db["output"]
                self.collection_output.create_index([ (self.VAR_ID,1) ])
            else:
                self.collection_output = self.db["output"]
        else:
            self.path_output = "Result/{}/{}".format(self.indicator, self.VAR)
            if not os.path.exists(self.path_output):
                os.makedirs(self.path_output)
                
        if self.indicator in ['atypicality','commonness','novelty','foster']:
            self.populate_list(**kwargs)
        else:
            print('''indicator must be in 'atypicality', 'commonness', 'novelty' ''')
        print('saved')
