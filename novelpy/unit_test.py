import os 
import tqdm
import pickle 
import numpy as np
import itertools
import scipy
import json
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse.linalg import norm
from scipy.sparse import csr_matrix, lil_matrix, triu
from novelpy.indicators.Wang2017 import get_difficulty_cos_sim
from novelpy.indicators.Wang2017 import get_difficulty_cos_sim_rame


difficulty_adj = np.array([[1, 40124, 3],
                           [40124, 5, 42],
                           [3, 42, 13352]])

"""
cx = csr_matrix(difficulty_adj).tocoo()    
x = lil_matrix((1, cx.shape[0]))
for i,j,v in itertools.izip(cx.row, cx.col, cx.data):
    (i,j,v)
"""
  
cos_sim = get_difficulty_cos_sim(csr_matrix(difficulty_adj))
cos_sim.todense()

cos_sim_sk = get_difficulty_cos_sim_rame(csr_matrix(difficulty_adj))
cos_sim_sk.todense()


num = 400000000013414*5 + 400000000013414
den = np.sqrt(float(400000000013414**2)+1)*np.sqrt(25+float(400000000013414**2))
cos_man = num/den



if cos_man == cos_sim[0,1]:
    print("nice")
    
type(csr_matrix(difficulty_adj).dot(csr_matrix(difficulty_adj))/csr_matrix(difficulty_adj))

np.array([1,2,3])/np.array([1,2,3])

import pymongo

Client = pymongo.MongoClient("mongodb://localhost:27017")
db = Client["novelty_sample"]
collection = db["Citation_net"]

docs = collection.find({})

pmid_list = []
for doc in tqdm.tqdm(docs):
    pmid_list.append(doc["PMID"])
    


docs = collection.find({})

n = 0
for doc in tqdm.tqdm(docs):
    if len(set(pmid_list).intersection(doc["refs_pmid_wos"]))>0:
        n += 1
    
    

Client = pymongo.MongoClient("mongodb://localhost:27017")
db = Client["novelty_sample"]
collection = db["Title_abs"]

docs = collection.find({"PMID":11327866})
doc = next(docs)
#{PMID:11327866}
#{PMID:8566773, PMID:10089522}


import json

collection_embedding = []
for year in tqdm.tqdm(range(1995,2001)):
    collection_embedding += json.load(open("Data/docs/embedding/{}.json".format(year)))
collection_embedding = {doc["PMID"]:{"title_embedding":doc["title_embedding"],"abstract_embedding":doc["abstract_embedding"]} for doc in collection_embedding}    



docs = json.load(open("Data/docs/references_embedding/{}.json".format(2003)))   
doc = [doc for doc in docs if doc["PMID"]==12475065][0]
refs = [collection_embedding[id_] for id_ in doc["refs_pmid_wos"] if id_ in collection_embedding]
ref = refs[0]
