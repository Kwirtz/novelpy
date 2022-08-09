import os
import tqdm
import json
import scipy
import pickle 
import numpy as np
import json
import novelpy
import unittest
import math

class TestUzzi(unittest.TestCase):
    
    def get_papers_items(self):
        self.papers_item = {5:[{"item": "A", "year": 3},
                              {"item": "C", "year": 1},
                              {"item": "D", "year": 2}],#NEWCOMB
                           6:[{"item": "B", "year": 0},
                              {"item": "C", "year": 1},
                              {"item": "B", "year": 0}]
                          }

        self.uzzi = novelpy.Uzzi2013(collection_name = 'Ref_journals',
                                    id_variable = 'id',
                                     year_variable = 'year',
                                     variable = 'Ref_journals',
                                     sub_variable = 'item',
                                     focal_year = 3,
                                     density = True)
    
    def test_get_data(self):
        self.get_papers_items()
        self.uzzi.get_data()
        print(self.uzzi.current_adj)
        self.assertDictEqual(d1 = self.uzzi.papers_items,
                             d2 = self.papers_item)

    def test_shuffle_network(self):
        self.get_papers_items()
        self.uzzi.get_data()
        self.sampled_current_items = novelpy.shuffle_network(self.papers_item)
        sampled_network = [['A', 'C', 'D'], ['B', 'C', 'B']]
        
        self.assertListEqual(self.sampled_current_items, 
                             sampled_network)
            
            
    def test_get_adjacency_matrix(self):
        self.get_papers_items()
        self.uzzi.get_data()
        self.sampled_current_items = novelpy.shuffle_network(self.papers_item)
        sampled_current_adj = novelpy.get_adjacency_matrix(self.uzzi.name2index,
                                                           self.sampled_current_items,
                                                           unique_pairwise = False,
                                                           keep_diag = True)

        adj_mat = np.array([[0,0,1,1],
                            [0,1,2,0],
                            [0,0,0,1],
                            [0,0,0,0]])
        np.testing.assert_array_equal(sampled_current_adj.A,
                                      adj_mat)      
        
    def test_get_unique_value_used(self):
        self.get_papers_items()
        self.uzzi.get_data()
        self.uzzi.sample_network()
        self.uzzi.get_all_adj()
        self.unique_values = novelpy.get_unique_value_used(self.uzzi.all_sampled_adj_freq)
        values = [(0, 2), (0, 3), (1, 1), (1, 2), (2, 3)]
        self.assertListEqual(self.unique_values,
                             values)
                             
    
    
    def test_get_comb_mean_sd(self):
        self.get_papers_items()
        self.uzzi.get_data()
        self.uzzi.sample_network()
        self.uzzi.get_all_adj()
        self.unique_values = novelpy.get_unique_value_used(self.uzzi.all_sampled_adj_freq)
        mean, sd = novelpy.get_comb_mean_sd(self.uzzi.path_score,
                                                  self.uzzi.all_sampled_adj_freq,
                                                  self.unique_values,
                                                  self.uzzi.variable,
                                                  self.uzzi.focal_year)
        
        mean_adj_mat = np.array([[0,0,1,1],
                            [0,1,2,0],
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
        self.get_papers_items()
        self.uzzi.get_data()      
        self.uzzi.sample_network()
        self.uzzi.compute_comb_score()
        comb_scores = pickle.load(open(self.uzzi.path_score + "/{}.p".format(self.uzzi.focal_year),"rb" ) )
        nan_mat = np.array([[ math.nan, math.nan, math.nan, math.nan],
                             [ 0, math.nan, math.nan, math.nan],
                             [ 0, 0, math.nan, math.nan],
                             [ 0,  0,  0, math.nan]])
        
        np.testing.assert_array_equal(comb_scores.A,
                                       nan_mat)
        
    def test_update_paper_values(self):
        self.get_papers_items()
        self.uzzi.get_data()      
        self.uzzi.sample_network()
        self.uzzi.compute_comb_score()
        self.uzzi.update_paper_values()
        score = json.load(open(self.uzzi.path_output+ "/{}.json".format(self.uzzi.focal_year),"r" ))
        nan_score = [{"id": 5,
                      "Ref_journals_uzzi": {"scores_array": [math.nan, math.nan, math.nan], 
                                            "score": {"conventionality": math.nan,
                                                      "novelty": math.nan}}},
                     {"id": 6,
                      "Ref_journals_uzzi": {"scores_array": [math.nan, math.nan, math.nan], 
                                            "score": {"conventionality": math.nan, 
                                                      "novelty": math.nan}}}
                    ]
        json.dump(nan_score,open(self.uzzi.path_output+ "/{}_test.json".format(self.uzzi.focal_year),"w" ))
        nan_score = json.load(open(self.uzzi.path_output+ "/{}_test.json".format(self.uzzi.focal_year),"r" ))
        self.assertListEqual(score,nan_score)