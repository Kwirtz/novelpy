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

class TestWang(unittest.TestCase):
        
    def get_papers_items(self):
        self.wang = novelpy.Wang2017(collection_name = 'Ref_journals',
                                            id_variable = 'id',
                                             year_variable = 'year',
                                             variable = 'Ref_journals',
                                             sub_variable = 'item',
                                             focal_year = 3)
        self.papers_item = docs3 = {5:[{"A", "C", "D"}],#NEWCOMB
                           6:[{"B", "C", "B"}]
                          }

    def test_get_data(self):
        self.get_papers_items()
        self.wang.get_data()

     

        self.assertDictEqual(d1 = self.wang.papers_items,d2 = self.papers_item)
