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




