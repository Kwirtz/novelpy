import os 
import tqdm
import scipy
import pickle 
import numpy as np
import scipy.sparse as sp
from scipy.sparse import csr_matrix, triu
from novelpy.utils.run_indicator_tools import create_output

# np.seterr(divide='ignore', invalid='ignore')

class Lee2015(create_output):

    def __init__(self,
             collection_name,
             id_variable,
             year_variable,
             variable,
             sub_variable,
             focal_year,
             client_name = None,
             db_name = None,
             density = False,
             list_ids = None,
             ram_efficient= False):
        """
        Description
        -----------
        Compute Commonness as proposed by Lee, Walsh, and Wang (2015)

        Parameters
        ----------
        var: str
            Variable used.
        collection_name: str
            Name of the collection or the json file containing the variable.  
        id_variable: str
            Name of the key which value give the identity of the document.
        year_variable : str
            Name of the key which value is the year of creation of the document.
        variable: str
            Name of the key that holds the variable of interest used in combinations.
        sub_variable: str
            Name of the key which holds the ID of the variable of interest (nested dict in variable).
        focal_year: int
            Calculate the novelty score for every document which has a year_variable = focal_year.
        client_name: str
            Mongo URI if your data is hosted on a MongoDB instead of a JSON file.
        db_name: str 
            Name of the MongoDB.
        density: bool 
            If True, save an array where each cell is the score of a combination. If False, save only the percentile of this array


        Returns
        -------
        None.

        """
        
        self.indicator = "lee"
        
        create_output.__init__(self,
                               client_name = client_name,
                               db_name = db_name,
                               collection_name = collection_name ,
                               id_variable = id_variable,
                               year_variable = year_variable,
                               variable = variable,
                               sub_variable = sub_variable,
                               focal_year = focal_year,
                               density = density,
                               list_ids = list_ids) 
        
        self.ram_efficient = ram_efficient
        self.path_score = "Data/score/lee/{}".format(variable)
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
        temp_adj = self.current_adj.T+triu(self.current_adj,k=1)
        ij_sums = np.sum(temp_adj.A, axis= 0)[np.newaxis]
        ij_sums = ij_sums.astype('uint64')        
        if self.ram_efficient:
            comb_scores = sp.lil_matrix((temp_adj.shape[0], temp_adj.shape[1]), dtype=np.float64)
            nonzero_rows, nonzero_cols = temp_adj.nonzero()
            for row, col in tqdm.tqdm(zip(nonzero_rows, nonzero_cols),total=len(nonzero_rows)):
                value = temp_adj[row, col]
                ij_products = ij_sums[0,row]*ij_sums.T[col,0]
                comb_scores[row,col] = value*int(Nt)/ij_products
            comb_scores = csr_matrix(comb_scores)
            
            comb_scores.data[np.isinf(comb_scores.data)] =  0
            comb_scores.data[np.isnan(comb_scores.data)] =  0
            comb_scores = triu(comb_scores,format='csr')
        else:
            ij_products = ij_sums.T.dot(ij_sums)
            self.ij_sums = ij_sums
            self.ij_products = ij_products
            
            print("comb_scores")
            comb_scores = csr_matrix((csr_matrix(temp_adj,dtype=float)*int(Nt))/ij_products)
            comb_scores.data[np.isinf(comb_scores.data)] = 0
            comb_scores.data[np.isnan(comb_scores.data)] =  0
            comb_scores = triu(comb_scores,format='csr')

        print("pickle dump")
        pickle.dump(comb_scores, open(self.path_score + "/{}.p".format(self.focal_year), "wb" ) )
        

    def get_indicator(self):

        self.get_data()      
        print('Getting the ', self.indicator, ' novelty score for combination of items in ', self.focal_year, ' ...')  
        self.compute_comb_score()
        print("Matrice done !")  
        print('Attributing the ',self.indicator, ' novelty indicator for ',self.focal_year '  papers ...')       
        self.update_paper_values()
        print("Done !")        
