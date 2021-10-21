import os 
import pickle 
import numpy as np
from scipy.sparse import csr_matrix, triu
from novelpy.utils.run_indicator_tools import create_output

# np.seterr(divide='ignore', invalid='ignore')

class Lee2015(create_output):

    def __init__(self, client_name = None,
             db_name = None,
             collection_name = None,
             id_variable = None,
             year_variable = None,
             variable = None,
             sub_variable = None,
             focal_year = None):
        """
        Description
        -----------
        Compute Commonness as proposed by Lee, Walsh, and Wang (2015)

        Parameters
        ----------
        current_adj : scipy.sparse.csr.csr_matrix
            The accumulated coocurence/adjacency matrix of items we want to calculate the novelty score on.
        focal_year : int
            Calculate novelty for object that have a creation/publication year = focal_year.
        variable : str
            Variable of interest (only for path purpose)

        Returns
        -------
        None.

        """
        
        self.indicator = "commonness"
        
        create_output.__init__(self,
                               client_name = client_name,
                               db_name = db_name,
                               collection_name = collection_name ,
                               id_variable = id_variable,
                               year_variable = year_variable,
                               variable = variable,
                               sub_variable = sub_variable,
                               focal_year = focal_year)
        

        self.path_score = "Data/score/commonness/{}".format(variable)
        if not os.path.exists(self.path_score):
            os.makedirs(self.path_score)
            
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
        
        pickle.dump(comb_scores, open(self.path_score + "/{}.p".format(self.focal_year), "wb" ) )
        

    def get_indicator(self):
        self.get_data()      
        print('Getting score per year ...')  
        self.compute_comb_score()
        print("Matrice done !")  
        print('Getting score per paper ...')       
        self.update_paper_values()
        print("Done !")        
