import os 
import tqdm
import json
import scipy
import pickle 
import numpy as np
import json
import novelpy
import unittest
#%% Create fake data

docs1 = [{'id':1,
          'year':1,
          'Ref_journals':[{"item": "A", "year": 0},
                          {"item": "B", "year": 1},
                          {"item": "B", "year": 0}]},
         {'id':2,
          'year':1,
          'Ref_journals':[{"item": "C", "year": 0},
                          {"item": "B", "year": 0},
                          {"item": "A", "year": 1}]},
        ]

docs2 = [{'id':3,
          'year':2,
          'Ref_journals':[{"item": "A", "year": 0},
                          {"item": "C", "year": 1},
                          {"item": "B", "year": 1}]},
         {'id':4,
          'year':2,
          'Ref_journals':[{"item": "D", "year": 0},
                          {"item": "C", "year": 1},
                          {"item": "B", "year": 2}]},
        ]


docs3 = [{'id':5,
          'year':3,
          'Ref_journals':[{"item": "A", "year": 0},
                          {"item": "C", "year": 1},
                          {"item": "D", "year": 1}]},#NEWCOMB
         {'id':6,
          'year':3,
          'Ref_journals':[{"item": "B", "year": 0},
                          {"item": "C", "year": 1},
                          {"item": "B", "year": 2}]},
        ]



docs4 = [{'id':7,
          'year':4,
          'Ref_journals':[{"item": "A", "year": 1},
                          {"item": "A", "year": 3},
                          {"item": "B", "year": 1}]},
         {'id':8,
          'year':4,
          'Ref_journals':[{"item": "D", "year": 3},
                          {"item": "C", "year": 1},
                          {"item": "A", "year": 2}]},#REUSED
        ]



docs5 = [{'id':9,
          'year':5,
          'Ref_journals':[{"item": "B", "year": 4},
                          {"item": "C", "year": 3},
                          {"item": "D", "year": 1}]},
         {'id':10,
          'year':5,
          'Ref_journals':[{"item": "A", "year": 0},
                          {"item": "C", "year": 1},
                          {"item": "A", "year": 4}]},
        ]

i=1
for docs in [docs1,docs2,docs3,docs4,docs5]:
    json.dump(docs,open('Data/docs/Ref_journals/{}.json'.format(str(i)),'w'))
    i+=1

#%% Create Fake cooc


ref_cooc = novelpy.utils.cooc_utils.create_cooc(
                 collection_name = "Ref_journals",
                 year_var="year",
                 var = "Ref_journals",
                 sub_var = "item",
                 time_window = range(1,5),
                 weighted_network = True, self_loop = True)

ref_cooc.main()


ref_cooc = novelpy.utils.cooc_utils.create_cooc(
                 collection_name = "Ref_journals",
                 year_var="year",
                 var = "Ref_journals",
                 sub_var = "item",
                 time_window = range(1,5),
                 weighted_network = False, self_loop = True)

ref_cooc.main()

ref_cooc = novelpy.utils.cooc_utils.create_cooc(
                 collection_name = "Ref_journals",
                 year_var="year",
                 var = "Ref_journals",
                 sub_var = "item",
                 time_window = range(1,5),
                 weighted_network = False, self_loop = False)

ref_cooc.main()



#%% Test Uzzi


        
        
#%% Test Lee

class TestLee(unittest.TestCase):
    
    def test_get_data(self):
        self.lee = novelpy.Lee2015(collection_name = 'Ref_journals',
                                    id_variable = 'id',
                                     year_variable = 'year',
                                     variable = 'Ref_journals',
                                     sub_variable = 'item',
                                     focal_year = 3)
        lee.get_data()

        papers_item = {5:[{"A", "C", "D"}],#NEWCOMB
                               6:[{"B", "C", "B"}]
                              }


        self.assertDictEqual(d1 = self.lee.papers_items,d2 = papers_item)

#%% Test Foster


class TestFoster(unittest.TestCase):
        
    def test_get_data(self):
        foster = novelpy.Foster2015(collection_name = 'Ref_journals',
                                    id_variable = 'id',
                                     year_variable = 'year',
                                     variable = 'Ref_journals',
                                     sub_variable = 'item',
                                     focal_year = 3)
        foster.get_data()

        papers_item =  {5:[{"A", "C", "D"}],#NEWCOMB
                               6:[{"B", "C", "B"}]
                              }


        self.assertDictEqual(d1 = foster.papers_items,d2 = papers_item)


#%% Test Wang

class TestWang(unittest.TestCase):
        
    def test_get_data(self):
        wang = novelpy.Wang2017(collection_name = 'Ref_journals',
                                    id_variable = 'id',
                                     year_variable = 'year',
                                     variable = 'Ref_journals',
                                     sub_variable = 'item',
                                     focal_year = 3)
        wang.get_data()

        papers_item = docs3 = {5:[{"A", "C", "D"}],#NEWCOMB
                               6:[{"B", "C", "B"}]
                              }


        self.assertDictEqual(d1 = wang.papers_items,d2 = papers_item)


difficulty_adj = np.array([[1, 40124, 3],
                           [40124, 5, 42],
                           [3, 42, 13352]])

"""
cx = csr_matrix(difficulty_adj).tocoo()    
x = lil_matrix((1, cx.shape[0]))
for i,j,v in itertools.izip(cx.row, cx.col, cx.data):
    (i,j,v)
"""
  
cos_sim = get_difficulty_cos_sim(csr_matrix(difficulty_adj))
cos_sim.todense()

cos_sim_sk = get_difficulty_cos_sim_rame(csr_matrix(difficulty_adj))
cos_sim_sk.todense()


num = 400000000013414*5 + 400000000013414
den = np.sqrt(float(400000000013414**2)+1)*np.sqrt(25+float(400000000013414**2))
cos_man = num/den



if cos_man == cos_sim[0,1]:
    print("nice")


#%% Test Wubu

#%% Test Shibayama

#%% Test AuthorProximity

