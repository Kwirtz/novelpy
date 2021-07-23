import numpy as np
import pickle 
from scipy.sparse import lil_matrix
from novelpy.indicators.utils import *

# Moslty used for Novelty
   
def sum_adj_matrix(time_window,path):
    
    unique_items = list(
        pickle.load(open( path + "/name2index.p", "rb" )).keys()) 
    matrix = lil_matrix((len(unique_items),len(unique_items)))
    
    for focal_year in tqdm.tqdm(time_window):
        fy_cooc = pickle.load(open( path + "/{}.p".format(focal_year), "rb" )) 
        matrix += fy_cooc 
        
    return matrix


def get_difficulty_cos_sim(difficulty_adj):
     
     difficulty_norms = np.apply_along_axis(norm, 0, difficulty_adj.A)[np.newaxis]
     difficulty_norms = difficulty_norms.T.dot(difficulty_norms)
     cos_sim = difficulty_adj.dot(difficulty_adj)/difficulty_norms
     cos_sim = csr_matrix(triu(np.nan_to_num(cos_sim)))
     cos_sim.setdiag(0)
     cos_sim.eliminate_zeros()
     return cos_sim
