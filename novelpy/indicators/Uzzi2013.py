from novelpy.utils.Uzzi2013_utils import *
from novelpy.utils.indicators_utils import *
import os
import pickle
from scipy.sparse import triu, csr_matrix
import tqdm
import re

class Atypicality:

    def __init__(self,
                 var,
                 var_year,
                 focal_year,
                 current_items,
                 unique_items,
                 true_current_adj_freq):
        """
        Description
        -----------
        Compute Atypicality as proposed by Uzzi, Mukherjee, Stringer and Jones (2013)
 
        Parameters
        ----------
        var : str
            variable used.
        var_year : str
            year variable name
        focal_year : int
            year of interest.
        current_item : dict
            dict with id as key and item and item info as value.
        unique_items : dict
            dict structured thi way name:index, file from the name2index.p generated with the cooccurrence matrices.
        true_current_adj_freq : scipy.sparse.csr.csr_matrix
            current adjacency matrix.

        Returns
        -------
        None.

        """
        self.current_items = current_items
        self.unique_items = unique_items
        self.true_current_adj_freq = true_current_adj_freq
        self.focal_year = focal_year
        self.var = var
        self.path1 = "Data/{}/sample_network/".format(self.var)
        self.path2 = "Data/{}/indicators_adj/atypicality/".format(self.var)
        if not os.path.exists(self.path1):
            os.makedirs(self.path1)
        if not os.path.exists(self.path2 + 'iteration/'):
            os.makedirs(self.path2 + 'iteration/')

    def sample_network(self,nb_sample):
        """
        

        Parameters
        ----------
        nb_sample : int
            number of sample to create.

        Returns
        -------
        None.

        """
        self.nb_sample = nb_sample
        allready_computed = [
            f for f in os.listdir(self.path1) 
                             if re.match(r'sample_[0-9]+_{}'.format(self.focal_year), f)
                             ]

        for i in tqdm.tqdm(range(nb_sample)):
            filename =  "sample_{}_{}.p".format(i,self.focal_year)
            if filename not in allready_computed:
                # Shuffle Network
                sampled_current_items = suffle_network(self.current_items)
                # Get Adjacency matrix
                sampled_current_adj = get_adjacency_matrix(self.unique_items,
                                                           sampled_current_items,
                                                           unique_pairwise = False,
                                                           keep_diag = True)
                pickle.dump(
                    sampled_current_adj,
                    open(self.path1 + filename,
                         "wb" ) )
                
    def compute_comb_score(self):
        """
               
        Description
        -----------
        Compute Atypicality Scores and store them on the disk

        Returns
        -------
        None.

        """
        # Get nb_sample networks
        all_sampled_adj_freq = []
        for i in tqdm.tqdm(range(self.nb_sample)):
            sampled_current_adj_freq = pickle.load(
                open(self.path1 + "sample_{}_{}.p".format(i,self.focal_year),
                "rb" ) )
            
            all_sampled_adj_freq.append(sampled_current_adj_freq)
        

        unique_values = get_unique_value_used(all_sampled_adj_freq)
        
        mean_adj_freq, sd_adj_freq = get_comb_mean_sd(self.path2,
                                                      all_sampled_adj_freq,
                                                      unique_values,
                                                      self.var,
                                                      self.focal_year)
        
        comb_scores = (self.true_current_adj_freq-mean_adj_freq)/sd_adj_freq  
        comb_scores[np.isinf(comb_scores)] =  0
        comb_scores[np.isnan(comb_scores)] =  0
        comb_scores = triu(comb_scores,format='csr')
        comb_scores.eliminate_zeros()
            
        pickle.dump(
            comb_scores,
            open(self.path2 + "/{}_{}.p".format('atypicality',
						self.focal_year),
                 "wb" ) )
        

