import novelpy
import os
import re
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import unittest

class TestShibayama(unittest.TestCase):
        
    def test_get_indicators(self):
            
        shibayama = novelpy.indicators.Shibayama2021(
                     collection_name = 'Ref_journals',
                     collection_embedding_name = 'articles_embedding',
                     id_variable = 'id',
                     year_variable = 'year',
                     ref_variable = 'refs_pmid_wos',
                     entity = ['title_embedding','abstract_embedding'],
                     focal_year = 3)

        shibayama.get_indicator()

        collection_embedding_acc = []
        all_years = [int(re.sub('.json','',file)) for file in os.listdir("Data/docs/{}/".format(shibayama.collection_embedding_name))]
        for year in all_years:
            collection_embedding_acc += json.load(open("Data/docs/{}/{}.json".format(shibayama.collection_embedding_name,year)))

        collection_embedding = {doc[shibayama.id_variable]:{shibayama.id_variable:doc[shibayama.id_variable],
                                   "title_embedding":doc["title_embedding"],
                                   "abstract_embedding":doc["abstract_embedding"]} for doc in collection_embedding_acc}

        titles_emb = []
        for i in [1,3,4]:
            titles_emb.append(collection_embedding[i]['title_embedding'])

        n = 3
        doc_mat = np.zeros((n,200))
        for i in range(n):
            item = titles_emb[i]
            if item:
                doc_mat[i, :] =  item

        dist_list = novelpy.similarity_dist(n,doc_mat = doc_mat,distance_fun = cosine_similarity)
        mean = np.mean(dist_list)
        nov_list = novelpy.get_percentiles(dist_list)
        self.assertEqual(nov_list['stats']['mean'],mean)