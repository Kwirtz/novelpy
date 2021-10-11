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
from multiprocessing import Process, Manager
import traceback
import sys
from .indicators_utils import *


def populate_list(idx = None,
                  var_id= None,
                  current_item = None ,
                  unique_items = None,
                  item_name = None,
                  indicator= None,
                  comb_scores = None,
                  tomongo = None,
                  client_name = None,
                  db_name = None,
                  collection_name = None,
                  docs_infos = None,
                  kwargs = None):
    """
    Description
    -----------

    Parameters
    ----------
    idx : int, optional
        id of the document. 
        The default is None.
    var_id : str, optional
        id variable name.
        The default is None.
    current_item : dict, optional
        dict with id as key and item and item info as value. 
        The default is None.
    unique_items : dict, optional
        dict structured thi way name:index, file from the name2index.p generated with the cooccurrence matrices.
        The default is None.
    item_name : str, optional
        variable used name.
        The default is None.
    indicator : str, optional
        indicator for which the score is computed. Works with 'atypicality', 'commonness' and 'novelty'.
        The default is None.
    comb_scores : scipy.sparse.csr.csr_matrix, optional
        indicator score adjacency matrix.
        The default is None.
    tomongo : bool, optional
        Wether you use mongo. The default is None.
    client_name : str, optional
        client name. The default is None.
    db_name : str, optional
        db name . The default is None.
    collection_name : str, optional
        collection name to update with indicators.
        The default is None.
    docs_infos : list, optional
        list to store results if not using mongo.
        The default is None.
    kwargs : keyword arguments, optional
        More argument for novelty as time_window or n_reutilisation.
        The default is None.

    Returns
    -------
    Update on mongo paper scores or store it in a dict

    """


    # try:
    if indicator in ['atypicality','novelty','commonness']:
        if len(current_item)>2:
            if indicator == 'atypicality':
                current_item = pd.DataFrame(current_item)['item'].tolist()
            if indicator != 'novelty':
                unique_pairwise = False
                keep_diag=True
            else:
                unique_pairwise = True
                keep_diag=False
            current_adj = get_adjacency_matrix(unique_items,
                                               [current_item],
                                               unique_pairwise = unique_pairwise,
                                               keep_diag = keep_diag)
           
            infos = get_paper_score(current_adj,
                                    comb_scores,
                                    list(unique_items.keys()),
                                    indicator,
                                    item_name,
                                    kwargs)
    elif 'new_infos' in kwargs:
        infos = kwargs['new_infos']
    try :
        if tomongo:
            client = pymongo.MongoClient(client_name)
            db = client[db_name]
            collection = db[collection_name]
            query = { var_id: int(idx) }
            newvalue =  { '$set': infos}
            collection.update_one(query,newvalue)
        else:
            docs_infos.append({int(idx):infos}) 
    except Exception as e:
        print(e)


class Dataset:
    
    def __init__(self,
                 var,
                 var_id,
                 var_year,
                 focal_year,
                 sub_var = None,
                 client_name = None,
                 db_name = None,
                 collection_name = None):
        """
        Description
        -----------
        Class to connect to the data set and query and update data in a very easy way.
        it also calculates scores for each paper with an adjacency matric for each document for indicators for which it is needed.
        update in done in parallel and use and available cores.
        
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
        self.focal_year = focal_year
        self.VAR_YEAR = var_year
        self.VAR_PMID = var_id
        self.VAR = var
        self.SUB_VAR = sub_var
        self.item_name = self.VAR.split('_')[0]
        self.client_name = client_name
        self.db_name = db_name
        self.collection_name = collection_name
        if client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            
        else:
            self.docs = pickle.load(open("/Data/{}.p".format(self.focal_year),
                                         "rb" ) )
            
        if not os.path.exists('Data/{}/results/'.format(self.VAR)):
            os.makedirs('Data/{}/results/'.format(self.VAR))

        

        
    def choose_path(self,
                    indicator):
        """
        Description
        -----------       
        Choose the appropriate path and load the name2index depending on the indicator

        Parameters
        ----------
        indicator : str
            indicator for which the score is computed

        Returns
        -------
            path to search for adjacency matrix and name2index
            name2index dict
        """
        unw = ['novelty']
        type1 = 'unweighted_network' if indicator in unw else 'weighted_network'
        type2 = 'no_self_loop' if indicator in unw else 'self_loop'
        self.path = "Data/{}/{}_{}".format(self.VAR,type1,type2)
        self.unique_items = pickle.load(open(self.path + "/name2index.p", "rb" ))

    
    def get_item_infos(self,
                       item,
                       indicator):
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
     
        if indicator == 'atypicality':
            if 'year' in item.keys():
                doc_item = {'item':item[self.SUB_VAR],
                                  'year':item['year']}
        elif indicator == 'kscores': 
            doc_item = item
        else:
            doc_item = item[self.SUB_VAR]
        
        return  doc_item
        
    
    def get_items(self,
                  indicator):
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
        current_items: dict
            dict with document id and item strucutured as needed

        """

        if self.client:
            self.docs = self.collection.find({
                self.VAR:{'$exists':'true'},
                self.VAR_YEAR:self.focal_year
                })
            
        if indicator in ['atypicality','novelty','commonness']:
            self.choose_path(indicator)    
            self.current_adj =  pickle.load(
                open(self.path+'/{}.p'.format(self.focal_year),
                     "rb" )) 

        current_items = dict()
        
        for items in tqdm.tqdm(self.docs):
            doc_items = list()
          
            for item in items[self.VAR]:
                ######### Get doc item and update journal list #########
                if self.SUB_VAR:
                    doc_item = self.get_item_infos(item,
                                                    indicator)
                    if doc_item:
                        doc_items.append(doc_item)
                else:
                    if items:
                        doc_items.append(item)
                    
            ######### Store items #########
            ### focal year items
            doc_items = list(doc_items)
            
            if items[self.VAR_YEAR] == self.focal_year:
                current_items.update({
                    int(items[self.VAR_PMID]):doc_items
                })  
        
        self.current_items = current_items


    def parallel_populate_list(self,indicator, kwargs, tomongo = False):
        """
     
        Description
        -----------        
        update document scores on mongo or save it in a file

        Parameters
        ----------
        indicator : str
            indicator for which the score is computed.
        kwargs : keyword arguments, optional
            More argument for novelty as time_window or n_reutilisation.
        tomongo : bool, optional
            Wether you use mongo. The default is False.

        Returns
        -------
            None

        """
        comb_scores = pickle.load(
                open(
                    'Data/{}/indicators_adj/{}/{}_{}.p'.format(
                        self.VAR,indicator,indicator,self.focal_year),
                    "rb" ))
            
        docs_infos = [] 
        with Manager() as manager:
            docs_infos = manager.list()
            processes = []
            
            for idx in tqdm.tqdm(list(self.current_items),desc='start'):
                
                p = Process(target=populate_list,
                            args=(idx,
                                  self.VAR_PMID,
                                  self.current_items[idx],
                                  self.unique_items,
                                  self.item_name,
                                  indicator,
                                  comb_scores,
                                  tomongo,
                                  self.client_name,
                                  self.db_name,
                                  self.collection_name,
                                  docs_infos,
                                  kwargs))
                p.start()
                processes.append(p)
    
            for p in tqdm.tqdm(processes,desc = 'join'):
                p.join()
            
            if not tomongo:
                print(docs_infos[10])
                pickle.dump(
                    list(docs_infos),
                    open(
                        'Data/{}/results/{}_{}.p'.format(
                            self.VAR, indicator,self.focal_year),
                          "wb" ) )

    def update_paper_values(self,indicator , tomongo = False, **kwargs):
        """

        Description
        -----------        
        run database update

        Parameters
        ----------
        indicator : str
            indicator for which the score is computed.
        tomongo : bool, optional
            Wether you use mongo. The default is False.
        **kwargs : keyword arguments, optional
            More argument for novelty as time_window or n_reutilisation.
            
        Returns
        -------
        None.

        """
        
        if indicator in ['atypicality','commonness','novelty']:
            
            self.parallel_populate_list(indicator , kwargs, tomongo = False)
            
        else:
            print('''indicator must be in 'atypicality', 'commonness', 'novelty' ''')
        print('saved')