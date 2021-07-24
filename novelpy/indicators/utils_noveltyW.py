import numpy as np
import pickle 
from scipy.sparse import lil_matrix, triu 
from utils import *
from scipy.linalg import norm

# Moslty used for Novelty
   
def sum_adj_matrix(time_window,path):
    """
    

    Parameters
    ----------
    time_window : int
        time window to compute the difficulty in the past and the reutilisation in the futur.
    path : str
        path to adjacency matrices.

    Returns
    -------
    matrix : scipy.sparse.csr.csr_matrix
        sum of considered matrices.

    """
    unique_items = list(
        pickle.load(open( path + "/name2index.p", "rb" )).keys()) 
    matrix = lil_matrix((len(unique_items),len(unique_items)))
    
    for focal_year in tqdm.tqdm(time_window):
        fy_cooc = pickle.load(open( path + "/{}.p".format(focal_year), "rb" )) 
        matrix += fy_cooc 
        
    return matrix


def get_difficulty_cos_sim(difficulty_adj):
     """
    

    Parameters
    ----------
    difficulty_adj : scipy.sparse.csr.csr_matrix
       summed past adjacency matrices used to compute the cosine similarity matrix

    Returns
    -------
    cos_sim : scipy.sparse.csr.csr_matrix
        cosine similarity matrix for each combination.

    """
     difficulty_norms = np.apply_along_axis(norm, 0, difficulty_adj.A)[np.newaxis]
     difficulty_norms = difficulty_norms.T.dot(difficulty_norms)
     cos_sim = difficulty_adj.dot(difficulty_adj)/difficulty_norms
     cos_sim = csr_matrix(triu(np.nan_to_num(cos_sim)))
     cos_sim.setdiag(0)
     cos_sim.eliminate_zeros()
     return cos_sim
