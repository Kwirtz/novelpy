from scipy.sparse import csr_matrix, lil_matrix, triu
from novelpy.utils.indicators_utils import *
import tqdm
import numpy as np
import pickle 
import os 
# np.seterr(divide='ignore', invalid='ignore')

class Commonness:

    def __init__(self,
                 var,
                 var_year,
                 focal_year,
                 current_adj):
        """
        Description
        -----------
        Compute Commonness as proposed by Lee, Walsh, and Wang (2015)

        Parameters
        ----------
        var : str
            variable used.
        var_year : str
            year variable name
        focal_year : int
            year of interest.
        current_adj : scipy.sparse.csr.csr_matrix
            current adjacency matrix.

        Returns
        -------
        None.

        """
        self.var = var
        self.var_year = var_year
        self.focal_year = focal_year
        self.current_adj = current_adj
        self.path2 = "Data/{}/indicators_adj/commonness/".format(var)
        if not os.path.exists(self.path2):
            os.makedirs(self.path2)
            
    def compute_comb_score(self):
        """
        
        Description
        -----------
        Compute Commonness Scores and store them on the disk

        Returns
        -------
        None.

        """
        
        Nt = np.sum(triu(self.current_adj))
        
        ij_sums = np.sum(self.current_adj.A, axis= 0)[np.newaxis]
        ij_products = ij_sums.T.dot(ij_sums)
        
        comb_scores = (csr_matrix(self.current_adj,dtype=float)*int(Nt))/ij_products
        comb_scores[np.isinf(comb_scores)] =  0
        comb_scores[np.isnan(comb_scores)] =  0
        comb_scores = triu(comb_scores,format='csr')
        
        pickle.dump(comb_scores, open(self.path2 + "/{}.p".format(self.focal_year), "wb" ) )
        


