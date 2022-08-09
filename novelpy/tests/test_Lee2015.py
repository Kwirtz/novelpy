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


class TestLee(unittest.TestCase):
    
    def get_papers_items(self):

        self.papers_item = {5:["A", "C", "D"],#NEWCOMB
                               6:["B", "C", "B"]
                              }

        self.lee = novelpy.Lee2015(collection_name = 'Ref_journals',
                                    id_variable = 'id',
                                    year_variable = 'year',
                                    variable = 'Ref_journals',
                                    sub_variable = 'item',
                                    focal_year = 3,
                                    density = True)
    
    def test_get_data(self):
        self.get_papers_items()
        self.lee.get_data()

        self.assertDictEqual(d1 = self.lee.papers_items,d2 = self.papers_item)

    def test_compute_comb_score(self):
        self.get_papers_items()
        self.lee.get_data()
        self.lee.compute_comb_score()
        print(self.lee.current_adj.A)
        N = 1+1+1+2+1
        adj_mat = np.array([[0,0,1,1],
                            [0,1,2,0],
                            [0,0,0,1],
                            [0,0,0,0]])

        Ni_mat = np.array([[2,2,2,2],
                            [3,3,3,3],
                            [4,4,4,4],
                            [2,2,2,2]])
        Nj_mat = np.array([[2,3,4,2],
                            [2,3,4,2],
                            [2,3,4,2],
                            [2,3,4,2]])
        numerator = adj_mat*N
        divider = np.multiply(Ni_mat,Nj_mat)
        comb_scores_test = np.divide(numerator,divider)

        comb_scores = pickle.load(open(self.lee.path_score + "/{}.p".format(self.lee.focal_year),"rb" ) ).A
        np.testing.assert_array_equal(comb_scores,comb_scores_test)


    def test_update_paper_values(self):
        self.get_papers_items()
        self.lee.get_data()
        self.lee.compute_comb_score()
        self.lee.update_paper_values()
        score = json.load(open(self.lee.path_output+ "/{}.json".format(self.lee.focal_year),"r" ))
        test_score = [{"id": 5,
                      "Ref_journals_lee": {"scores_array": [0.75,1.5,0.75], 
                                            "score": {"novelty": -np.log(np.quantile([0.75,1.5,0.75],0.1))}}},
                     {"id": 6,
                      "Ref_journals_lee": {"scores_array": [1.0,2/3,1.0], 
                                            "score": {"novelty": -np.log(np.quantile([1,2/3,1],0.1))}}}
                    ]
        json.dump(test_score,open(self.lee.path_output+ "/{}_test.json".format(self.lee.focal_year),"w" ))
        test_score = json.load(open(self.lee.path_output+ "/{}_test.json".format(self.lee.focal_year),"r" ))
        self.assertListEqual(score,test_score)
