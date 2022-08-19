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
from sklearn.metrics.pairwise import cosine_similarity
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
                                       density = True,
				       keep_item_percentile = 0)
        self.papers_item = docs3 = {5:["A", "C", "D"],#NEWCOMB
                           6:["B", "C", "B"]
                          }

    def test_get_data(self):
        self.get_papers_items()
        self.wang.get_q_journal_list()
        self.wang.get_data()


        self.assertDictEqual(d1 = self.wang.papers_items,d2 = self.papers_item)


    def test_adj(self):
        self.get_papers_items()
        self.wang.get_q_journal_list()
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

    def test_adj2(self):
        #cos_sim = get_difficulty_cos_sim(self.difficulty_adj)
        #comb_scores = self.futur_adj.multiply(nbd_adj).multiply(cos_sim)

        self.get_papers_items()
        self.wang.get_q_journal_list()
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


    def test_get_difficulty_cos_sim(self):
        #cos_sim = get_difficulty_cos_sim(self.difficulty_adj)
        #comb_scores = self.futur_adj.multiply(nbd_adj).multiply(cos_sim)

        self.get_papers_items()
        self.wang.get_q_journal_list()
        self.wang.get_data()

        difficulty_adj = np.array([[0,3,2,0],
                            [0,0,3,1],
                            [0,0,0,1],
                            [0,0,0,0]])
        cos_sim = novelpy.get_difficulty_cos_sim(difficulty_adj)

        test_difficulty_adj = np.array([[0,3,2,0],
                                        [3,0,3,1],
                                        [2,3,0,1],
                                        [0,1,1,0]])
        cos_sim_test = csr_matrix(triu(cosine_similarity(test_difficulty_adj,dense_output=False),k=1))
        np.testing.assert_array_equal(cos_sim_test.A,cos_sim.A)

    def test_compute_comb_score(self):

        self.get_papers_items()
        self.wang.get_q_journal_list()
        self.wang.get_data()
        self.wang.compute_comb_score()

        comb_scores = pickle.load(open(self.wang.path_score + "/{}.p".format(self.wang.focal_year),"rb" ) ).A
        value_AD = cosine_similarity([[0,1,1,0],[0,3,2,0]])[0,1]
        comb_scores_test = np.array([[0,0,0,1-value_AD],
                            [0,0,0,0],
                            [0,0,0,0],
                            [0,0,0,0]])
        np.testing.assert_array_equal(comb_scores_test,comb_scores)
        


    def test_update_paper_values(self):
        self.get_papers_items()
        self.wang.get_q_journal_list()
        self.wang.get_data()
        self.wang.compute_comb_score()
        self.wang.update_paper_values()

        value_AD = cosine_similarity([[0,1,1,0],[0,3,2,0]])[0,1]

        score = json.load(open(self.wang.path_output+ "/{}.json".format(self.wang.focal_year),"r" ))
        test_score = [{"id": 5,
                      "Ref_journals_wang_2_1_restricted0": {"scores_array": [1-value_AD,0.0,0.0], 
                                            "score": {"novelty": 1-value_AD}}},
                     {"id": 6,
                      "Ref_journals_wang_2_1_restricted0": {"scores_array": [0.0], 
                                            "score": {"novelty": 0.0}}}
                    ]
        json.dump(test_score,open(self.wang.path_output+ "/{}_test.json".format(self.wang.focal_year),"w" ))
        test_score = json.load(open(self.wang.path_output+ "/{}_test.json".format(self.wang.focal_year),"r" ))
        self.assertListEqual(score,test_score)
