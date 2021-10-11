from scipy.sparse import csr_matrix, lil_matrix
import tqdm
import pickle 
import os 
import numpy as np
import pickle 
from scipy.sparse import lil_matrix, triu, csr_matrix
from scipy.linalg import norm
import tqdm 

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

class Novelty:


    def __init__(self,
                 var,
                 var_year,
                 focal_year,
                 time_window,
                 n_reutilisation):
        """
        
        Description
        -----------
        Compute Novelty as proposed by Wang, Veugelers and Stephan (2017)

        Parameters
        ----------
        var : str
            variable used.
        var_year : str
            year variable name
        focal_year : int
            year of interest.
        time_window : int
            time window to compute the difficulty in the past and the reutilisation in the futur.
        n_reutilisation : int
            minimal number of reutilisation in the futur.

        Returns
        -------
        None.

        """
        
        self.var = var
        self.focal_year = focal_year
        self.time_window = time_window
        self.n_reutilisation = n_reutilisation
        self.path = 'Data/{}/unweighted_network_no_self_loop/'.format(self.var)
        self.path2 = "Data/{}/indicators_adj/novelty/".format(self.var)
        if not os.path.exists(self.path):
            os.makedirs(self.path)        
        if not os.path.exists(self.path2):
            os.makedirs(self.path2)

    def get_matrices_sums(self):
        """
        
        Description
        -----------
        Agglomerate futur and past matrix to compute difficulty for never been made combinations

        Returns
        -------
        None.

        """
        print('calculate past matrix')
        self.past_adj = sum_adj_matrix(range(1980,
                                        self.focal_year),
                                  self.path)

        print('calculate futur matrix')
        self.futur_adj = sum_adj_matrix(range(self.focal_year+1,
                                        self.focal_year+self.time_window+1),
                                  self.path)

        print('calculate difficulty matrix')
        self.difficulty_adj = sum_adj_matrix(range(self.focal_year-self.time_window,
                                            self.focal_year),
                                  self.path)

    def compute_comb_score(self):
        """
        
        Description
        -----------
        Compute Novelty Scores and store them on the disk

        Returns
        -------
        None.

        """
        # Never been done
        nbd_adj = lil_matrix(self.past_adj.shape)
        mask = np.ones(self.past_adj.shape, dtype=bool)
        mask[self.past_adj.nonzero()] = False
        nbd_adj[mask] = 1
        
        # Reused after
        self.futur_adj[self.n_reutilisation < self.futur_adj] = 0
        self.futur_adj[self.futur_adj >= self.n_reutilisation] = 1
        self.futur_adj = csr_matrix(self.futur_adj)
        self.futur_adj.eliminate_zeros()
        # Create a matrix with the cosine similarity
        # for each combinaison never made before but reused in the futur
        cos_sim = get_difficulty_cos_sim(self.difficulty_adj)
        comb_scores = self.futur_adj.multiply(nbd_adj).multiply(cos_sim)
        comb_scores[comb_scores.nonzero()] = 1 - comb_scores[comb_scores.nonzero()]        
                    
        pickle.dump(
            comb_scores,
            open(self.path2 + "{}_{}.p".format('novelty',
						self.focal_year),
                 "wb" ) )
        
