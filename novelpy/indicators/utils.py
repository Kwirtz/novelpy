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


def get_adjacency_matrix(unique_items,
                         items_list,
                         unique_pairwise,
                         keep_diag):
    """
    
    Description
    -----------
    Compute adjacency matrix for single and multiple document

    Parameters
    ----------
    unique_items : dict
        dict structured thi way name:index, file from the name2index.p generated with the cooccurrence matrices.
    items_list : list 
        list of list, each element of the list is the list of the item used
    unique_pairwise : bool
        to take into account multiple edges
    keep_diag : bool
        keep diagonal

    Returns
    -------
    adj_mat : scipy.sparse.csr.csr_matrix
        adjacency matrix in csr format

    """
    
    if unique_pairwise:     
        lb = preprocessing.MultiLabelBinarizer(classes=sorted(list(unique_items.keys())))
        dtm_mat = lil_matrix(lb.fit_transform(items_list))
        adj_mat = dtm_mat.T.dot(dtm_mat)
    else:
        adj_mat = lil_matrix((len(unique_items.keys()),len(unique_items.keys())), dtype = np.uint32)
        for item in items_list:
            for combi in list(combinations(item, r=2)):
                combi = sorted(combi)
                ind_1 = unique_items[combi[0]]
                ind_2 = unique_items[combi[1]]
                adj_mat[ind_1,ind_2] += 1
                adj_mat[ind_2,ind_1] += 1          
    adj_mat = lil_matrix(adj_mat)
    if keep_diag == False:
        adj_mat.setdiag(0)
    adj_mat = adj_mat.tocsr()
    adj_mat.eliminate_zeros()
    return adj_mat


        
        
def get_paper_score(doc_adj,comb_scores,unique_items,indicator,item_name,kwargs):
    """

    Description
    -----------
    Compute scores for a document and store indicators scores in a dict

    Parameters
    ----------
    doc_adj : scipy.sparse.csr.csr_matrix
        document adjacency matrix.
    comb_scores : scipy.sparse.csr.csr_matrix
        indicator score adjacency matrix.
    unique_items : dict
        dict structured thi way name:index, file from the name2index.p generated with the cooccurrence matrices.
    indicator : str
        indicator for which the score is computed. Works with 'atypicality', 'commonness' and 'novelty'
    item_name : str
        variable used name.
    kwargs : keyword arguments
        More argument for novelty as time_window or n_reutilisation

    Returns
    -------
    dict
        scores and indicators infos.

    """
    doc_comb_adj = lil_matrix(doc_adj.multiply(comb_scores))
    unique_comb_idx = triu(doc_comb_adj,k=0).nonzero() if indicator in ['atypicality','commonness'] else triu(doc_comb_adj,k=1).nonzero()

    comb_idx = [[],[]]
    for i, j in zip(list(unique_comb_idx[0]),
                    list(unique_comb_idx[1])):
        n = int(doc_adj[i,j])
        for c in range(n):
            comb_idx[0].append(i)
            comb_idx[1].append(j)
    
    comb_infos = pd.DataFrame([
        {'item1':sorted(unique_items)[i],
        'item2':sorted(unique_items)[j],
        'score':doc_comb_adj[i,j]/int(doc_adj[i,j])
            } for i,j in zip(comb_idx[0],comb_idx[1])])
    
    if comb_idx[0]:
        comb_list = comb_infos.score.tolist()
        comb_infos = comb_infos.groupby(['item1','item2','score']).size().reset_index()
        comb_infos = comb_infos.rename(columns = {0:'count'}).to_dict('records')
        
    if isinstance(comb_infos, pd.DataFrame):
        comb_infos = comb_infos if not comb_infos.empty else None

    key = item_name+'_'+indicator
    if 'n_reutilisation' and 'time_window' in kwargs:
        key = key +'_'+str(kwargs['time_window'])+'y_'+str(kwargs['n_reutilisation'])+'reu'
    elif 'time_window' in kwargs:
        key = key +'_'+str(kwargs['time_window'])+'y'
       
    doc_infos = {'nb_comb':len(comb_infos) if comb_infos else 0,
                 'comb_infos': comb_infos}
    
    if indicator == 'novelty':
        score = {'novelty':sum(comb_list) if comb_idx[0] else 0}
        
    elif indicator == 'atypicality':
        score = {'conventionality': np.median(comb_list) if comb_idx[0] else None,
                 'novelty': np.quantile(comb_list,0.1) if comb_idx[0] else None}
        
    elif indicator == 'commonness':
        score = {'novelty': -np.log(np.quantile(comb_list,0.1)) if comb_idx[0] else None}
            
    doc_infos.update({'score':score })
    return {key:doc_infos}

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
            self.docs = pickle.load(open("/Data/{}/{}.p".format(self.VAR_YEAR,
                                                                   self.focal_year),
                                         "rb" ) )
            
        if not os.path.exists('Data/{}/{}/results/'.format(self.VAR_YEAR,
                                                           self.VAR)):
            os.makedirs('Data/{}/{}/results/'.format(self.VAR_YEAR,
                                                     self.VAR))

        

        
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
        self.path = "Data/{}/{}/{}_{}".format(self.VAR_YEAR,self.VAR,type1,type2)
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
                    'Data/Journal_JournalIssue_PubDate_Year/{}/indicators_adj/{}/{}_{}.p'.format(
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
                        'Data/Journal_JournalIssue_PubDate_Year/{}/results/{}_{}.p'.format(
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
