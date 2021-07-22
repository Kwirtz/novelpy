import pymongo
import glob
import tqdm
import numpy as np
import time
from sklearn import preprocessing
from scipy.sparse import csr_matrix, triu 
from scipy.linalg import norm
from joblib import Parallel, delayed

class Indicators:
    
    def __init__(self,
                 client_name,
                 db_name,
                 collection_name,
                 var,
                 sub_var):
        
        self.client = pymongo.MongoClient(client_name)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        if 'wos' in collection_name:
            self.VAR_YEAR = 'PY'
            self.VAR_PMID = 'PM'
        elif 'articles' in collection_name:
            self.VAR_YEAR = 'Journal_JournalIssue_PubDate_Year'
            self.VAR_PMID = 'PMID'
        self.VAR = var
        self.SUB_VAR = sub_var
    
        
    ####### INDICATORS #######
    
    def update_mongo(pmid,
                     doc_items,
                     collection):
    
        query = { 'PM': int(pmid) }
        doc_infos = get_paper_score(doc_items)
        newvalues = { '$set': doc_infos}
        collection.update_one(query,newvalues)
        
        
def par_novelty(focal_year = 1976,window = 3):
    
    var = 'CR_year_category'
    wosdata = Indicators(client_name = 'mongodb://localhost:27017',db_name = 'Pubmed',collection_name = 'wos_pkg',var = 'CR_year_category',sub_var = 'journal')
    
    docs = wosdata.collection.find({
        var:{'$exists' : 'true'},
        'PY':{'$lt':str(focal_year+window)}
        })

    wosdata.Novelty(docs,
                    focal_year,
                    window,
                    restrict_wos_journal = True,
                    insert_mongo = True)
    
    

if __name__ == '__main__':
    #years = np.arange(1975,1980)
    #windows = [3,4,5]
    #Parallel(n_jobs=-1
    #         )(delayed(par_novelty
    #                   )(year,window) for year, window in zip(np.repeat(years,len(windows)),
    #                                                          windows*len(years)))
    focal_year = 1979
    
    var = 'CR_year_category'
    wosdata = Indicators(client_name = 'mongodb://localhost:27017',
                         db_name = 'Pubmed',
                         collection_name = 'wos_pkg',
                         var = 'CR_year_category',
                         sub_var = 'journal')
    
    docs = wosdata.collection.find({
        var:{'$exists' : 'true'},
        'PY':str(focal_year)}
        )
    items = wosdata.get_items(docs,
                              focal_year,
                              indicator = 'atypicality',
                              restrict_wos_journal = True)
        
# 'novelty' 661087 1min30
