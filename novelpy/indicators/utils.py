import numpy as np
from sklearn import preprocessing
from scipy.sparse import csr_matrix, triu, lil_matrix
from scipy.linalg import norm
from itertools import combinations, chain
import pandas as pd
from random import sample
import tqdm
import networkx as nx
import pymongo
import time
import pickle
from joblib import Parallel, delayed
import json
import time
import os

def get_comb(item):
    combi = [tuple(sorted(comb)) for comb in combinations(item,2)]
    return combi
    

def get_adjacency_matrix(unique_items,
                         items_list,
                         unique_pairwise,
                         keep_diag):
    
    if unique_pairwise:     
        lb = preprocessing.MultiLabelBinarizer(classes=sorted(list(unique_items.keys())))
        dtm_mat = csr_matrix(lb.fit_transform(items_list))
        adj_mat = dtm_mat.T.dot(dtm_mat)
    else:
        
        adj_mat = lil_matrix((len(unique_items.keys()),len(unique_items.keys())), dtype = np.uint32)
        for item in tqdm.tqdm(items_list):
            for combi in list(combinations(item, r=2)):
                combi = sorted(combi)
                ind_1 = unique_items[combi[0]]
                ind_2 = unique_items[combi[1]]
                adj_mat[ind_1,ind_2] += 1
                adj_mat[ind_2,ind_1] += 1
            
    if keep_diag == False:
        adj_mat.setdiag(0)
    adj_mat = adj_mat.tocsr()
    adj_mat.eliminate_zeros()
    return adj_mat


        
        
def get_paper_score(doc_adj,comb_scores,unique_items,indicator,item_name,**kwargs):
    
    doc_comb_adj = csr_matrix(doc_adj.multiply(comb_scores))
    
    unique_comb_idx = triu(doc_comb_adj,k=0).nonzero() if indicator in ['atypicality','commonness'] else triu(doc_comb_adj,k=1).nonzero()
    
    comb_idx = [[],[]]
    for i, j in zip(list(unique_comb_idx[0]),
                    list(unique_comb_idx[1])):
        n = int(doc_adj[i,j])
        for c in range(n):
            comb_idx[0].append(i)
            comb_idx[1].append(j)
    
    
    
    comb_infos = pd.DataFrame([
        {
            'item1':sorted(unique_items)[i],
            'item2':sorted(unique_items)[j],
            'score':doc_comb_adj[i,j]/int(doc_adj[i,j])
            } 
        for i,j in zip(comb_idx[0],comb_idx[1])]
        )
    
    if comb_idx[0]:
        comb_list = comb_infos.score.tolist()
        
        comb_infos = comb_infos.groupby(['item1','item2','score']).size().reset_index()
        comb_infos = comb_infos.rename(columns = {0:'count'}).to_dict('records')
    if isinstance(comb_infos, pd.DataFrame):
        comb_infos = comb_infos if not comb_infos.empty else None

    key = item_name+'_'+indicator
    if 'n_reutilisation' and 'window' in kwargs:
        key = key +'_'+kwargs['window']+'y_'+kwargs['n_reutilisation']+'reu'
    elif 'window' in kwargs:
        key = key +'_'+kwargs['window']+'y'
       
    doc_infos = {
        'nb_comb':len(comb_infos) if comb_infos else 0,
        'comb_infos': comb_infos
        }
    
    
    if indicator == 'novelty':
        score = {'novelty':sum(comb_list) if comb_idx[0] else 0}
    elif indicator == 'atypicality':
        score = {'conventionality': np.median(comb_list) if comb_idx[0] else None,
                 'novelty': np.quantile(comb_list,0.1) if comb_idx[0] else None
                 }
    elif indicator == 'commonness':
        score = {'novelty': -np.log(np.quantile(comb_list,0.1)) if comb_idx[0] else None}
            
        
    doc_infos.update({
        'score':score
        })
    
    return {key:doc_infos}



class Dataset:
    
    def __init__(self,
        client_name = None,
        db_name = None,
        collection_name = None,
        var = None,
        sub_var = None,
        focal_year = None):
        
        self.focal_year = focal_year
        if 'wos' in collection_name:
            self.VAR_YEAR = 'PY'
            self.VAR_PMID = 'PM'
        elif 'articles' in collection_name:
            self.VAR_YEAR = 'Journal_JournalIssue_PubDate_Year'
            self.VAR_PMID = 'PMID'
        self.VAR = var
        self.SUB_VAR = sub_var
        self.item_name = self.VAR.split('_')[0]
        if client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
        else:
            self.docs = pickle.load(open("/Data/{}/{}/{}.p".format(self.VAR_YEAR,
                                                                   self.VAR,
                                                                   self.focal_year),
                                         "rb" ) )
            
        if not os.path.exists('Data/Journal_JournalIssue_PubDate_Year/{}/results/'.format(self.VAR)):
            os.makedirs('Data/Journal_JournalIssue_PubDate_Year/{}/results/'.format(self.VAR))

        

        
    def choose_path(self,indicator):
        unw = ['novelty']
        type1 = 'unweighted_network' if indicator in unw else 'weighted_network'
        type2 = 'no_self_loop' if indicator in unw else 'self_loop'
        self.path = "Data/{}/{}/{}_{}".format(self.VAR_YEAR,self.VAR,type1,type2)
        self.unique_items = pickle.load(open(self.path + "/name2index.p", "rb" ))

    
    def get_item_infos(self,
                       item,
                       indicator,
                       restrict_wos_journal):
        
        if restrict_wos_journal:
            if 'category' in item.keys():
                if indicator == 'atypicality':
                    if 'year' in item.keys():
                        doc_item = {'journal':item[self.SUB_VAR],
                                          'year':item['year']}
                else:
                    doc_item = item[self.SUB_VAR]    
                    
                return all_item, doc_item
            
        else:
            if indicator == 'atypicality':
                if 'year' in item.keys():
                    doc_item = {'item':item[self.SUB_VAR],
                                      'year':item['year']}
            else:
                doc_item = item[self.SUB_VAR]
            
            return  doc_item
        return  []
    
    def get_items(self,
                  indicator,
                  restrict_wos_journal = False):

        if self.client:
            self.docs = self.collection.find({
                self.VAR:{'$exists':'true'},
                self.VAR_YEAR:self.focal_year
                })
        self.choose_path(indicator)
        self.true_adj =  pickle.load(
            open( self.path+'/{}.p'.format(self.focal_year),
                 "rb" )) 

        ######### Set Objects #########
        current_items = dict()
        
        ######### Iterate over documents #########
        for items in tqdm.tqdm(self.docs):
            doc_items = list()
          
            for item in items[self.VAR]:
                ######### Get doc item and update journal list #########
                doc_item = self.get_item_infos(item,
                                                indicator,
                                                restrict_wos_journal)
                if doc_item:
                    doc_items.append(doc_item)
                
            ######### Store items #########
            ### focal year items
            doc_items = list(doc_items)
            
            if items[self.VAR_YEAR] == self.focal_year:
                current_items.update({
                    str(items[self.VAR_PMID]):doc_items
                })  
        
        self.current_items = current_items



    def populate_list(self,idx,current_item,unique_items,item_name,indicator,scores_adj,tomongo):
        if len(current_item)>2:
                try:
                    
                    if indicator == 'atypicality':
                        current_item = pd.DataFrame(current_item)['item'].tolist()
                    
                    current_adj = get_adjacency_matrix(unique_items,
                                                       [current_item],
                                                       unique_pairwise = False,
                                                       keep_diag=True)
        
                    infos = get_paper_score(current_adj,
                                            scores_adj,
                                            list(unique_items.keys()),
                                            indicator,
                                            item_name)
                    if tomongo:
                        update_mongo(idx,infos)
                    else:
                        return {idx:infos}
                    
                except Exception as e:
                    print(e)
 

  
    def update_paper_values(self,indicator, tomongo = False):
        comb_scores = pickle.load(
            open('Data/Journal_JournalIssue_PubDate_Year/{}/indicators_adj/{}/{}_{}.p'.format(self.VAR,
                                                                                              indicator,
                                                                                              indicator,
                                                                                              self.focal_year),
                 "rb" ) )
       
            
        
        docs_infos = Parallel(n_jobs=4)(
            delayed(self.populate_list)(idx,
                                    self.current_items[idx],
                                    self.unique_items,
                                    self.item_name,
                                    indicator,
                                    comb_scores,
                                    tomongo) for idx in tqdm.tqdm(self.current_items.keys()))
        if not tomongo:
            pickle.dump(
                docs_infos,
                open('Data/Journal_JournalIssue_PubDate_Year/{}/results/{}_{}.p'.format(self.VAR,indicator,self.focal_year),
                      "wb" ) )
            
        print('saved')


    def update_mongo(self,
                     pmid,
                     doc_infos):
    
        query = { self.VAR_PMID: int(pmid) }
        newvalues = { '$set': doc_infos}
        self.collection.update_one(query,newvalues)

