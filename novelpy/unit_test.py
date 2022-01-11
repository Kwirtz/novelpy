import os 
import tqdm
import pickle 
import numpy as np
from scipy.linalg import norm
from scipy.sparse import csr_matrix, lil_matrix, triu
from novelpy.indicators.Wang2017 import get_difficulty_cos_sim

difficulty_adj = np.array([[1, 400000000013414, 0],
                           [0, 5, 0],
                           [0, 0, 133333341355153415]])

num = 400000000013414*5 + 400000000013414
den = np.sqrt(float(400000000013414**2)+1)*np.sqrt(25+float(400000000013414**2))
cos_man = num/den

cos_sim = get_difficulty_cos_sim(csr_matrix(difficulty_adj))
cos_sim.todense()

if cos_man == cos_sim[0,1]:
    print("nice")



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