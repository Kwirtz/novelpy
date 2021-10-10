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

