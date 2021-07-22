from graphs.indicators.utils import * 
from graphs.indicators.commonness import *
import tqdm 
import time

indicator = 'commonness'


items = {'unique_items' : {'A','B','C','D','E'},
         'current_items':{
             '1':['A','B','B'],
             '2':['A','D','E'],
             '3':['C','D']
             }}


## Commonness
current_adj = get_adjacency_matrix(items['unique_items'],
                                   items['current_items'].values(),
                                   unique_pairwise = False,
                                   keep_diag=True)

current_adjs = {
    idx:get_adjacency_matrix(items['unique_items'],
                             [items['current_items'][idx]],
                             unique_pairwise = False,
                             keep_diag=True)
    for idx in tqdm.tqdm(items['current_items'])
    }


scores_adj = Commonness(current_adj)


docs_infos = {}
for idx in current_adjs:
    docs_infos.update({
        idx:get_paper_score(current_adjs[idx],
                            scores_adj,
                            items['unique_items'],
                            indicator)
        })
docs_infos


#### NOVELTY TEST WITH MONGO

indicator = 'commonness'
focal_year = 1975
var = 'CR_year_category'

data = Dataset(client_name = 'mongodb://localhost:27017', 
               db_name = 'Pubmed',
               collection_name = 'wos_pkg',
               var = var,
               sub_var = 'journal')
docs = data.collection.find({
    var:{'$exists':'true'},
    'PY':{'$eq':str(focal_year)}
    }
    )
items = data.get_items(docs,
                       focal_year,
                       indicator,
                       restrict_wos_journal = True)


t = time.time()
current_adj = get_adjacency_matrix(items['unique_items'],
                                   items['current_items'].values(),
                                   unique_pairwise = False,
                                   keep_diag=True)
time.time() - t 

t = time.time()
scores_adj = Commonness(current_adj)
time.time() - t 

for idx in tqdm.tqdm(items['current_items']):
    if len(items['current_items'][idx])>2:
        current_adj = get_adjacency_matrix(items['unique_items'],
                                           [items['current_items'][idx]],
                                           unique_pairwise = False,
                                           keep_diag=True)
        
        infos = get_paper_score(current_adj,
                                scores_adj,
                                items['unique_items'],
                                indicator)
        data.update_mongo(idx,infos)
        

