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
        self.papers_item = {5:[{"item": "A", "year": 3},
                              {"item": "C", "year": 1},
                              {"item": "D", "year": 2}],#NEWCOMB
                           6:[{"item": "B", "year": 0},
                              {"item": "C", "year": 1},
                              {"item": "B", "year": 0}]
                          }

        self.lee = novelpy.Lee2015(collection_name = 'Ref_journals',
                                    id_variable = 'id',
                                    year_variable = 'year',
                                    variable = 'Ref_journals',
                                    sub_variable = 'item',
                                    focal_year = 3)
    
    def test_get_data(self):
        self.get_papers_items
        self.lee.get_data()

        papers_item = {5:[{"A", "C", "D"}],#NEWCOMB
                               6:[{"B", "C", "B"}]
                              }


        self.assertDictEqual(d1 = self.lee.papers_items,d2 = papers_item)
