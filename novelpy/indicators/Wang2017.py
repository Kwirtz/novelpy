import os 
import pickle 
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix, lil_matrix, triu, tril
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
    
    difficulty_adj = triu(difficulty_adj,1) + tril(difficulty_adj.T)
    cos_sim = cosine_similarity(difficulty_adj,dense_output=False)
    cos_sim = csr_matrix(triu(np.nan_to_num(cos_sim)))
    cos_sim.setdiag(0)
    cos_sim.eliminate_zeros()
    return cos_sim

class Wang2017(create_output):


    def __init__(self,
                 collection_name,
                 id_variable,
                 year_variable,
                 variable,
                 sub_variable,
                 focal_year,
                 time_window_cooc,
                 n_reutilisation,
                 starting_year = None,
                 client_name = None,
                 db_name = None,
                 keep_item_percentile = 50,
                 density = False,
                 list_ids = None):
        """
        
        Description
        -----------
        Compute Novelty as proposed by Wang, Veugelers and Stephan (2017)

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
            If True, save an array where each cell is the score of a combination. If False, save only the percentiles of this array
        time_window_cooc : int
            time window to compute the difficulty in the past and the reutilisation in the futur.
        n_reutilisation : int
            minimal number of reutilisation in the futur.
        keep_item_percentile: int
            Between 0 and 100. Keep only items that appear more than keep_item_percentile% of every items

        Returns
        -------
        None.

        """
        self.indicator = "wang"
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
                               n_reutilisation = n_reutilisation,
                               starting_year = starting_year,
                               density = density,
                               keep_item_percentile = keep_item_percentile,
                               list_ids = list_ids)        

        self.path_score = "Data/score/wang/{}/".format(self.variable + "_" + str(self.time_window_cooc) + "_" + str(self.n_reutilisation)+ self.restricted )
       
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
        self.nbd_adj = lil_matrix(self.past_adj.shape, dtype="int8")
        mask = np.ones(self.past_adj.shape, dtype=bool)
        mask[self.past_adj.nonzero()] = False
        self.nbd_adj[mask] = 1
        self.nbd_adj = triu(self.nbd_adj,k=1)

        # Reused after
        self.futur_adj[self.futur_adj < self.n_reutilisation] = 0
        self.futur_adj[self.futur_adj >= self.n_reutilisation] = 1
        self.futur_adj = csr_matrix(self.futur_adj)
        self.futur_adj.eliminate_zeros()

        # Create a matrix with the cosine similarity
        # for each combinaison never made before but reused in the futur

        self.cos_sim = get_difficulty_cos_sim(self.difficulty_adj)

        comb_scores = self.futur_adj.multiply(self.nbd_adj).multiply(self.cos_sim)
        comb_scores[comb_scores.nonzero()] = 1 - comb_scores[comb_scores.nonzero()]   
                    
        pickle.dump(comb_scores, open(self.path_score + "{}.p".format(self.focal_year), "wb" ) )
        

    def get_indicator(self):
        self.get_q_journal_list()
        self.get_data()      
        print('Getting score per year ...')  
        self.compute_comb_score()
        print("Matrice done !")  
        print('Getting score per paper ...')  
        self.update_paper_values()
        print("Done !")   
