import novelpy
import os
import re
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import unittest

class TestAuthor_proximity(unittest.TestCase):
       
    def get_data(self):
        self.ap = novelpy.indicators.Author_proximity(
                         collection_name = 'Ref_journals',
                         id_variable = 'id',
                         year_variable = 'year',
                         aut_list_variable = 'a02_authorlist',
                         aut_id_variable = 'AID',
                         entity = ['title','abstract'],
                         focal_year = 4,
                         windows_size = 5,
                         density = False,
                 distance_type = 'cosine')
        
        self.ap.load_data()

        self.doc = {'id':8,
               'year':4,
               'a02_authorlist':[{'AID':2},
                                 {'AID':1}],
         }

        self.ap.compute_score(self.doc)

 
    def test_get_indicators_intra(self):
        self.get_data()
        self.ap.get_author_papers(2)

        test = [paper for year in self.ap.profile for paper in year['embedded_title']]
        dist_list = [1-cosine_similarity(np.array([test[0]]),np.array([test[1]])),
                    1-cosine_similarity(np.array([test[0]]),np.array([test[2]])),
                    1-cosine_similarity(np.array([test[1]]),np.array([test[2]]))]

        mean = np.mean(dist_list)
        score_mean = self.ap.infos['authors_novelty_title_5']['individuals_scores'][0]['stats']['mean']
        self.assertEqual(score_mean,mean)
 
    def test_get_indicators_inter(self):
        self.get_data()

        self.ap.get_author_papers(2)
        item = [paper for year in self.ap.profile for paper in year['embedded_title']]

        self.ap.get_author_papers(1)
        j_item =  [paper for year in self.ap.profile for paper in year['embedded_title']]
         
        dist_list = [1-1,
                1-cosine_similarity(np.array([item[0]]),np.array([j_item[1]])),
                1-cosine_similarity(np.array([item[0]]),np.array([j_item[2]])),
                1-1,
                
                1-cosine_similarity(np.array([item[1]]),np.array([j_item[0]])),
                1-cosine_similarity(np.array([item[1]]),np.array([j_item[1]])),
                1-cosine_similarity(np.array([item[1]]),np.array([j_item[2]])),
                1-cosine_similarity(np.array([item[1]]),np.array([j_item[3]])),
                
                1-cosine_similarity(np.array([item[2]]),np.array([j_item[0]])),
                1-cosine_similarity(np.array([item[2]]),np.array([j_item[1]])),
                1-1,
                1-cosine_similarity(np.array([item[2]]),np.array([j_item[3]]))]

        dist_list = [float(num) for num in dist_list]

        mean = np.mean(dist_list)
        score_mean = self.ap.infos['authors_novelty_title_5']['iter_individuals_scores'][0]['stats']['mean']
        self.assertEqual(score_mean,mean)