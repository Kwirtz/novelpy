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
import networkx as nx

class TestFoster(unittest.TestCase):
    
    def get_papers_items(self):

        self.papers_item = {5:["A", "C", "D"],#NEWCOMB
                               6:["B", "C", "B"]
                              }

        self.foster = novelpy.Foster2015(collection_name = 'Ref_journals',
                                       id_variable = 'id',
                                       year_variable = 'year',
                                       variable = "Ref_journals",
                                       sub_variable = "item",
                                       focal_year = 3,
                                       starting_year = 1,
                                       community_algorithm = "Louvain",
                                       density = True)
    
    def test_get_data(self):
        self.get_papers_items()
        self.foster.get_data()

        self.assertDictEqual(d1 = self.foster.papers_items,d2 = self.papers_item)

    def test_adj(self):
        self.get_papers_items()
        self.foster.get_data()
        adj1 =  np.array([[0,3,1,0],
                        [0,1,1,0],
                        [0,0,0,0],
                        [0,0,0,0]])

        adj2 =  np.array([[0,1,1,0],
                        [0,0,2,1],
                        [0,0,0,1],
                        [0,0,0,0]])

        test_adj = adj1+adj2
        np.testing.assert_array_equal(self.foster.current_adj.A,
                                      test_adj)



    def test_run_iteration(self):
        self.get_papers_items()
        self.foster.get_data()
        self.foster.g = nx.from_scipy_sparse_matrix(self.foster.current_adj, edge_attribute='weight')     
        self.foster.generate_commu_adj_matrix()
        self.foster.run_iteration()
        test_df = np.array([[1, 1, 1, 1],
                             [0, 1, 1, 1],
                             [0, 0, 1, 1],
                             [0, 0, 0, 1]])

        np.testing.assert_array_equal(self.foster.df.A,
                                      test_df)

    def test_update_paper_values(self):
        self.get_papers_items()
        self.foster.get_data()
        self.foster.g = nx.from_scipy_sparse_matrix(self.foster.current_adj, edge_attribute='weight')     
        self.foster.generate_commu_adj_matrix()
        self.foster.run_iteration()
        self.foster.save_score_matrix()
        self.foster.update_paper_values()

        comb_scores = pickle.load(open(self.foster.path_score + "/{}.p".format(self.foster.focal_year),"rb" ) ).A
        print(comb_scores)
        score = json.load(open(self.foster.path_output+ "/{}.json".format(self.foster.focal_year),"r" ))
        test_score = [{"id": 5,
                      "Ref_journals_foster": {"scores_array": [0.0,0.0,0.0], 
                                            "score": {"novelty": 0.0}}},
                     {"id": 6,
                      "Ref_journals_foster": {"scores_array": [0.0,0.0,0.0], 
                                            "score": {"novelty": 0.0}}}
                    ]
        json.dump(test_score,open(self.foster.path_output+ "/{}_test.json".format(self.foster.focal_year),"w" ))
        test_score = json.load(open(self.foster.path_output+ "/{}_test.json".format(self.foster.focal_year),"r" ))
        self.assertListEqual(score,test_score)