import os 
import tqdm
import json
import scipy
import pickle 
import itertools
import numpy as np
from scipy.sparse.linalg import norm
import community as community_louvain
from scipy.sparse import csr_matrix, lil_matrix, triu
from sklearn.metrics.pairwise import cosine_similarity
from novelpy.indicators.Wang2017 import get_difficulty_cos_sim
from novelpy.indicators.Wang2017 import get_difficulty_cos_sim_rame


#%% Test Uzzi


#%% Test Foster


#%% Test Wang


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


#%% Test Wubu

#%% Test Shibayama

#%% Test AuthorProximity

