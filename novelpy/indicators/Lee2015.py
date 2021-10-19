from scipy.sparse import csr_matrix, triu
import numpy as np
import pickle 
import os 

# np.seterr(divide='ignore', invalid='ignore')

class Lee2015():

    def __init__(self,
                 current_adj,
                 variable,
                 focal_year):
        """
        Description
        -----------
        Compute Commonness as proposed by Lee, Walsh, and Wang (2015)

        Parameters
        ----------
        current_adj : scipy.sparse.csr.csr_matrix
            current adjacency matrix.
        variable : str
            variable used.
        focal_year : int
            year of interest.

        Returns
        -------
        None.

        """
        self.varriable = variable
        self.focal_year = focal_year
        self.current_adj = current_adj
        self.path2 = "Data/score/commonness/{}".format(variable)
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
        


