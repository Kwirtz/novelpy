import scipy.sparse as sp 
import tqdm
import numpy as np
import pickle 
np.seterr(divide='ignore', invalid='ignore')

class Commonness:

    def __init__(self,
                 var,
                 current_adj,
                 focal_year):
        
        self.current_adj = current_adj
        self.path2 = "Data/Journal_JournalIssue_PubDate_Year/{}/indicators_adj/commonness/".format(self.var)
        if not os.path.exists(self.path2):
            os.makedirs(self.path2)
            
    def compute_comb_score(self):
        
        
        Nt = np.sum(sp.triu(self.current_adj))
        
        ij_sums = np.sum(current_adj.A, axis= 0)[np.newaxis]
        ij_products = ij_sums.T.dot(ij_sums)
        
        comb_scores = (csr_matrix(current_adj,dtype=float)*int(Nt))/ij_products
        comb_scores[np.isinf(comb_scores)] =  0
        comb_scores[np.isnan(comb_scores)] =  0
        comb_scores = sp.triu(comb_scores,format='csr')
        
        pickle.dump(
            comb_scores,
            open(self.path2 + "/{}_{}.p".format('commonness',
						self.focal_year),
                 "wb" ) )
        


