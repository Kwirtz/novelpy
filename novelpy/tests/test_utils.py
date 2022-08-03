import os 
import tqdm
import json
import scipy
import pickle 
import unittest
import itertools
import numpy as np
from scipy.sparse.linalg import norm
import community as community_louvain
from scipy.sparse import csr_matrix, lil_matrix, triu
from sklearn.metrics.pairwise import cosine_similarity
from novelpy.utils.cooc_utils import *


#%% Test cooc

paper_1 = {"id": 1, "Ref_journals": [{"item": "1"},{"item": "2"}], "year": 1990}
paper_2 = {"id": 1, "Ref_journals": [{"item": "1"},{"item": "2"},{"item": "3"}], "year": 1991}
paper_3 = {"id": 1, "Ref_journals": [{"item": "2"}], "year": 1991}
paper_4 = {"id": 1, "Ref_journals": [{"item": "4"},{"item": "3"}], "year": 1992}
paper_5 = {"id": 1, "Ref_journals": [{"item": "1"},{"item": "2"},{"item": "3"},{"item": "4"}], "year": 1992}
docs = [paper_1, paper_2, paper_3, paper_4, paper_5]



class Test(unittest.TestCase):
    

    def test_get_item_list(self):
        instance = create_cooc(var = "Ref_journals",
                               sub_var = "item",
                               year_var = "year",
                               collection_name = "no_need",
                               time_window = range(1990,1996),
                               dtype = np.uint16)
        
        item_list = ["1","2","3","4"]
        instance.get_item_list(docs)
        self.assertEqual(instance.item_list, item_list)
        
        
    def test_populate_matrix(self):
        pass 
"""
    def test_populate_matrix_no_self_loop(self):
        self.assertEquals(cube('abc'), 8)
"""

      

