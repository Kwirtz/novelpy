from package.indicators.utils import * 
from package.indicators.novelty import Novelty
from itertools import combinations

window = 3
indicator = 'novelty'

items = {'unique_items' : {'A','B','C','D','E'},
         'current_items':{
             '1':['A','B'],
             '2':['A','D','E'],
             '3':['C','D']
             },
         'past_items':[['A','B'],['A','D','B'],['A','C','C'],['A','D','B'],['A','C','E']],
         'difficulty_items':[['A','D','B'],['A','C','E']],
         'futur_items':[['C','B'],['A','D','E'],['D','C',]]
         }

## Novely

past_adj = get_adjacency_matrix(items['unique_items'],
                                items['past_items'],
                                unique_pairwise = True,
                                keep_diag=False)

futur_adj = get_adjacency_matrix(items['unique_items'],
                                 items['futur_items'],
                                 unique_pairwise = True,
                                 keep_diag=False)

difficulty_adj = get_adjacency_matrix(items['unique_items'],
                                      items['difficulty_items'],
                                      unique_pairwise = True,
                                      keep_diag=False)

scores_adj = Novelty(past_adj,
                     futur_adj,
                     difficulty_adj,
                     n_reutilisation = 1)

# Get score for each document
current_adjs = {
    idx:get_adjacency_matrix(items['unique_items'],
                             [items['current_items'][idx]],
                             unique_pairwise = True,
                             keep_diag=False)
    for idx in tqdm.tqdm(items['current_items'])
    }

docs_infos = {}
for idx in current_adjs:
    docs_infos.update({
        idx:get_paper_score(current_adjs[idx],
                            scores_adj,
                            items['unique_items'],
                            indicator,
                            window = str(window),
                            n_reutilisation = str(1))
        })
docs_infos
        
        
#### NOVELTY TEST WITH MONGO
indicator = 'novelty'

focal_year = 2016
window = 3
db  = 'pkg'

data = Dataset(client_name = pars['client_name'], 
               db_name =  pars['db_name'],
               collection_name = pars[db]['collection_name'],
               var = pars[db]['ref']['var'],
               sub_var = pars[db]['ref']['sub_var'])

docs = data.collection.find({
    pars[db]['ref']['var']:{'$exists':'true'},
    pars[db]['year_var']:{'$lt':str(focal_year+window)}
    }
    )

items = data.get_items(docs,
                       focal_year, 
                       indicator,
                       window, 
                       restrict_wos_journal = True)


past_adj = get_adjacency_matrix(items['unique_items'],
                                items['past_items'],
                                unique_pairwise = True,
                                keep_diag=False)

futur_adj = get_adjacency_matrix(items['unique_items'],
                                 items['futur_items'],
                                 unique_pairwise = True,
                                 keep_diag=False)

difficulty_adj = get_adjacency_matrix(items['unique_items'],
                                      items['difficulty_items'],
                                      unique_pairwise = True,
                                      keep_diag=False)

scores_adj = Novelty(past_adj,futur_adj,difficulty_adj,1)

for idx in tqdm.tqdm(items['current_items']):
    current_adj = get_adjacency_matrix(items['unique_items'],
                                       [items['current_items'][idx]],
                                       unique_pairwise = True,
                                       keep_diag=False)
    
    infos = get_paper_score(current_adj,
                            scores_adj,
                            items['unique_items'],
                            indicator,
                            item_name = 'journal',
                            window = str(window),
                            n_reutilisation = str(1))
    data.update_mongo(idx,infos)
        

