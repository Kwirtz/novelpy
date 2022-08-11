
import tqdm
import json
import scipy
import pickle 
import numpy as np
import json
import novelpy
import unittest
import math

class TestDisruptiveness(unittest.TestCase):
    
    def test_compute_scores(self):
        disruptiveness = novelpy.Disruptiveness(collection_name = 'Ref_journals',
                                                focal_year= 2,
                                                id_variable = 'id',
                                                refs_list_variable = 'refs',
                                                cits_list_variable = 'cited_by',
                                                year_variable = 'year')
        disruptiveness.get_citation_network()
        results = disruptiveness.compute_scores(3,[1, 2],[4, 5, 6, 9])

        J = len({4,6})
        I = len({5,9})
        K = len({8})
        Jxc = sum([2,0,1,0])
        J5 = len({})
        Breadth = len({4,5,9})
        Depth = len({6})

        score = {'id':3,
                'disruptiveness':{
                  'DI1': (I-J)/(I+J+K) ,
                  'DI5': (I-J5)/(I+J5+K),
                  'DI5nok': (I-J5)/(I+J5),
                  'DI1nok': (I-J)/(I+J),
                  'DeIn': Jxc/(I+J),
                  'Breadth': Breadth/(I+J) ,
                  'Depth': Depth/(I+J)}}


        self.assertDictEqual(d1 = results,
                             d2 = score)