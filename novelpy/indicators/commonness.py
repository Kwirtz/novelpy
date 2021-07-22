from .utils import *
import scipy.sparse as sp 
import tqdm
import numpy as np

np.seterr(divide='ignore', invalid='ignore')

def Commonness(current_adj):
    
    
    Nt = np.sum(sp.triu(current_adj))
    
    ij_sums = np.sum(current_adj.A, axis= 0)[np.newaxis]
    ij_products = ij_sums.T.dot(ij_sums)
    
    comb_scores = (current_adj*Nt)/ij_products
    comb_scores[np.isinf(comb_scores)] =  0
    comb_scores[np.isnan(comb_scores)] =  0
    comb_scores = sp.triu(comb_scores,format='csr')
    
    return comb_scores

