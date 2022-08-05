import os 
import tqdm
import json
import scipy
import pickle 
import itertools
import numpy as np
from scipy.sparse.linalg import norm
import community as community_louvain
from scipy.sparse import csr_matrix, lil_matrix, triu
from sklearn.metrics.pairwise import cosine_similarity
from novelpy.indicators.Wang2017 import get_difficulty_cos_sim
from novelpy.indicators.Wang2017 import get_difficulty_cos_sim_rame

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
import json
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



class TestUzzi(unittest.TestCase):
    
    def __init__(self):
        self.papers_item = {5:[{"item": "A", "year": 3},
                              {"item": "C", "year": 1},
                              {"item": "D", "year": 2}],#NEWCOMB
                           6:[{"item": "B", "year": 0},
                              {"item": "C", "year": 1},
                              {"item": "B", "year": 0}]
                          }
    
    def test_get_data(self):
        self.uzzi = novelpy.Uzzi2013(collection_name = 'Ref_journals',
                                    id_variable = 'id',
                                     year_variable = 'year',
                                     variable = 'Ref_journals',
                                     sub_variable = 'item',
                                     focal_year = 3)
        self.uzzi.get_data()
        
        self.assertDictEqual(d1 = self.uzzi.papers_items,
                             d2 = self.papers_item)

    def test_shuffle_network(self):
        self.sampled_current_items = novelpy.shuffle_network(self.papers_item)
        sampled_network = [['A', 'C', 'D'], ['B', 'C', 'B']]
        
        self.assertListEqual(self.sampled_current_items, 
                             sampled_network)
            
            
    def test_get_adjacency_matrix(self):
        sampled_current_adj = novelpy.get_adjacency_matrix(self.uzzi.name2index,
                                                           self.sampled_current_items,
                                                           unique_pairwise = False,
                                                           keep_diag = True)

        adj_mat = np.array([[0,0,1,1],
                            [0,2,2,0],
                            [0,0,0,1],
                            [0,0,0,0]])
        np.testing.assert_array_equal(sampled_current_adj.A,
                                      adj_mat)      
        
    def test_get_unique_value_used(self):
        self.uzzi.sample_network()
        self.uzzi.get_all_adj()
        self.unique_values = novelpy.get_unique_value_used(self.uzzi.all_sampled_adj_freq)
        values = [(0, 2), (0, 3), (1, 1), (1, 2), (2, 3)]
        self.assertListEqual(self.unique_values,
                             values)
                             
    
    
    def test_get_comb_mean_sd(self):
        mean, sd = novelpy.get_comb_mean_sd(self.uzzi.path_score,
                                                  self.uzzi.all_sampled_adj_freq,
                                                  self.unique_values,
                                                  self.uzzi.variable,
                                                  self.uzzi.focal_year)
        
        mean_adj_mat = np.array([[0,0,1,1],
                            [0,2,2,0],
                            [0,0,0,1],
                            [0,0,0,0]])
        
        sd_adj_mat = np.array([[0,0,0,0],
                        [0,0,0,0],
                        [0,0,0,0],
                        [0,0,0,0]])
        
        np.testing.assert_array_equal(mean.A,
                                      mean_adj_mat)
        np.testing.assert_array_equal(sd.A,
                                      sd_adj_mat)

    
    def test_compute_comb_score(self):
        self.uzzi.compute_comb_score()
        comb_scores = pickle.load(open(self.uzzi.path_score + "/{}.p".format(self.uzzi.focal_year),"rb" ) )
        nan_mat = np.array([[ math.nan, math.nan, math.nan, math.nan],
                             [ 0, math.nan, math.nan, math.nan],
                             [ 0, 0, math.nan, math.nan],
                             [ 0,  0,  0, math.nan]])
        
        np.testing.assert_array_equal(comb_scores.A,
                                       nan_mat)
        
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

