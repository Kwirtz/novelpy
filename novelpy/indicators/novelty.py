from .utils import *
import scipy.sparse as sp 
import tqdm

def Novelty(past_adj,
            futur_adj,
            difficulty_adj,
            n_reutilisation):
    
    # Never been done
    nbd_adj = sp.lil_matrix(past_adj.shape)
    mask = np.ones(past_adj.shape, dtype=bool)
    mask[past_adj.nonzero()] = False
    nbd_adj[mask] = 1
    
    # Reused after
    futur_adj[n_reutilisation < futur_adj] = 0
    futur_adj[futur_adj >= n_reutilisation] = 1
    futur_adj = sp.csr_matrix(futur_adj)
    futur_adj.eliminate_zeros()
    # Create a matrix with the cosine similarity
    # for each combinaison never made before but reused in the futur
    cos_sim = get_difficulty_cos_sim(difficulty_adj)
    comb_scores = futur_adj.multiply(nbd_adj).multiply(cos_sim)
    comb_scores[comb_scores.nonzero()] = 1 - comb_scores[comb_scores.nonzero()]        
    
    return comb_scores
