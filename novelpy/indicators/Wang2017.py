import os 
import tqdm
import pickle 
import numpy as np
from scipy.linalg import norm
from scipy.sparse import csr_matrix, lil_matrix, triu
from novelpy.utils.run_indicator_tools import create_output
   
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

class Wang2017(create_output):


    def __init__(self,
                 client_name = None,
                 db_name = None,
                 collection_name = None,
                 id_variable = None,
                 year_variable = None,
                 variable = None,
                 sub_variable = None,
                 focal_year = None,
                 time_window_cooc = None,
                 n_reutilisation = None):
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
        self.indicator = "novelty"
        create_output.__init__(self,
                               client_name = client_name,
                               db_name = db_name,
                               collection_name = collection_name ,
                               id_variable = id_variable,
                               year_variable = year_variable,
                               variable = variable,
                               sub_variable = sub_variable,
                               focal_year = focal_year,
                               time_window_cooc = time_window_cooc,
                               n_reutilisation = n_reutilisation)        

        self.path_score = "Data/score/novelty/{}/".format(self.variable + "_" + str(self.time_window_cooc) + "y_" + str(self.n_reutilisation) + "reu" )
        if not os.path.exists(self.path_score):
            os.makedirs(self.path_score)        

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
                    
        pickle.dump(comb_scores, open(self.path_score + "{}.p".format(self.focal_year), "wb" ) )
        

    def get_indicator(self):
        self.get_data()      
        print('Getting score per year ...')  
        self.compute_comb_score()
        print("Matrice done !")  
        print('Getting score per paper ...')  
        self.update_paper_values()
        print("Done !")   
