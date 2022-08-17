import novelpy
import os
import re
import json
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import unittest

class TestAuthor_proximity(unittest.TestCase):
        
    def test_get_indicators(self):

        ap = novelpy.indicators.Author_proximity(
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

        ap.load_data()

        doc = {'id':8,
                  'year':4,
                 'a02_authorlist':[{'AID':2},{'AID':1}],
         }

        ap.compute_score(doc)

        collection_embedding_acc = []
        all_years = [int(re.sub('.json','',file)) for file in os.listdir("Data/docs/{}/".format('articles_embedding'))]
        for year in all_years:
            collection_embedding_acc += json.load(open("Data/docs/{}/{}.json".format('articles_embedding',str(4))))

        collection_embedding = {doc[shibayama.id_variable]:{ap.id_variable:doc[ap.id_variable],
                                   "title_embedding":doc["title_embedding"],
                                   "abstract_embedding":doc["abstract_embedding"]} for doc in collection_embedding_acc}

        titles_emb = []
        for i in [1,4,5]:
            titles_emb.append(collection_embedding[i]['title_embedding'])

        n = 3
        doc_mat = []
        for i in range(n):
            item = titles_emb[i]
            if item:
                doc_mat.append(item)

        dist_list = [1-cosine_similarity(np.array([doc_mat[0]]),np.array([doc_mat[1]])),
                    1-cosine_similarity(np.array([doc_mat[0]]),np.array([doc_mat[2]])),
                    1-cosine_similarity(np.array([doc_mat[1]]),np.array([doc_mat[2]]))]

        mean = np.mean(dist_list)
        self.assertEqual(ap.infos['authors_novelty_title_5']['individuals_scores'][0]['stats']['mean'],mean)