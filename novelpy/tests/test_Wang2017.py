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
from scipy.sparse import csr_matrix, lil_matrix, triu, tril

class TestWang(unittest.TestCase):
        
    def get_papers_items(self):
        self.wang = novelpy.Wang2017(collection_name = 'Ref_journals',
                                       id_variable = 'id',
                                       year_variable = 'year',
                                       variable = "Ref_journals",
                                       sub_variable = "item",
                                       focal_year = 3,
                                       time_window_cooc = 2,
                                       starting_year = 1,
                                       n_reutilisation = 1,
                                       density = True)
        self.papers_item = docs3 = {5:["A", "C", "D"],#NEWCOMB
                           6:["B", "C", "B"]
                          }

    def test_get_data(self):
        self.get_papers_items()
        self.wang.get_data()


        self.assertDictEqual(d1 = self.wang.papers_items,d2 = self.papers_item)


    def test_adj(self):
        self.get_papers_items()
        self.wang.get_data()

        difficulty_adj = np.array([[0,3,2,0],
                            [0,0,3,1],
                            [0,0,0,1],
                            [0,0,0,0]])

        past_adj = np.array([[0,3,2,0],
                            [0,0,3,1],
                            [0,0,0,1],
                            [0,0,0,0]])

        futur_adj = np.array([[0,1,2,1],
                            [0,0,1,1],
                            [0,0,0,2],
                            [0,0,0,0]])

        np.testing.assert_array_equal(difficulty_adj,self.wang.difficulty_adj.A)
        np.testing.assert_array_equal(past_adj,self.wang.past_adj.A)
        np.testing.assert_array_equal(futur_adj,self.wang.futur_adj.A)

    def test_compute_comb_score(self):
        #cos_sim = get_difficulty_cos_sim(self.difficulty_adj)
        #comb_scores = self.futur_adj.multiply(nbd_adj).multiply(cos_sim)

        self.get_papers_items()
        self.wang.get_data()
        self.wang.compute_comb_score()

        nbd_adj = np.array([[0,0,0,1],
                            [0,0,0,0],
                            [0,0,0,0],
                            [0,0,0,0]])

        futur_adj = np.array([[0,1,1,1],
                            [0,0,1,1],
                            [0,0,0,1],
                            [0,0,0,0]])


        np.testing.assert_array_equal(nbd_adj,self.wang.nbd_adj.A)
        np.testing.assert_array_equal(futur_adj,self.wang.futur_adj.A)