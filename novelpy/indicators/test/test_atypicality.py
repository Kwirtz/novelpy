from novelpy.graphs.indicators.utils import * 
from novelpy.graphs.indicators.atypicality import *
import yaml 
with open("mongo_config.yaml", "r") as infile:
    pars = yaml.safe_load(infile)['PC_PP']


indicator = 'atypicality'

items = {'unique_items' : {'A','B','C','D','E'},
         'current_items':{
             '1':[{'journal': 'A', 'year': '1'},
                  {'journal': 'B', 'year': '2'},
                  {'journal': 'B', 'year': '3'}],
             
             '2':[{'journal': 'A', 'year': '2'},
                  {'journal': 'B', 'year': '2'},
                  {'journal': 'D', 'year': '1'}],
             
             '3':[{'journal': 'C', 'year': '2'},
                  {'journal': 'B', 'year': '2'},
                  {'journal': 'E', 'year': '1'}],
             }
         }

## Atypicality
true_current_items = {
    pmid:[items['current_items'][pmid][i]['journal']
     for i in range(len(items['current_items'][pmid]))] 
    for pmid in tqdm.tqdm(items['current_items'])
}

true_current_adj = get_adjacency_matrix(items['unique_items'],
                                        true_current_items,
                                        unique_pairwise = False,
                                        keep_diag =True)



scores_adj = Atypicality(true_current_adj,
                         items['current_items'],
                         items['unique_items'],
                         nb_sample = 50)


docs_infos = {}
for idx in items['current_items']:
    current_adj = get_adjacency_matrix(items['unique_items'],
                                       [true_current_items[idx]],
                                       unique_pairwise = False,
                                       keep_diag=True)
    
    infos = get_paper_score(current_adj,
                            scores_adj,
                            items['unique_items'],
                            indicator)
    docs_infos.update({idx:infos})
docs_infos
