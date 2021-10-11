from novelpy.utils.indicators_utils import *
import os
import pickle
from scipy.sparse import triu, csr_matrix
import tqdm
import re
import pandas as pd
import pickle
from scipy.sparse import lil_matrix
from random import sample
import tqdm
import numpy as np

pd.options.mode.chained_assignment = None

def suffle_network(current_items):
    """
    
    Description
    -----------
    list of list of items resampled conserving the distribution in time of the citations

    Parameters
    ----------
    current_items : list
        list of list of items

    Returns
    -------
    random_network : list
        list of list of items

    """
    lst = []
    for idx in current_items:
        for item in current_items[idx]:
          lst.append({'idx':idx,
                      'item':item['item'],
                      'year': item['year']})  
    df = pd.DataFrame(lst)    
    print('start sampling')
    years = set(df.year)
    for year in  years:
        journals_y = list(df.item[df.year == year])
        df.item[df.year == year] = sample(journals_y,k = len(journals_y))

    random_network = list(df.groupby('idx')['item'].apply(list))

    return random_network
        
def get_unique_value_used(all_sampled_adj_freq):
    """
    
    Description
    -----------
    Get the set of coordinates for which calculation is need to compute the mean and the standard deviation

    Parameters
    ----------
    all_sampled_adj_freq : list
        list of sampled adjacency matrices

    Returns
    -------
    list 
        list of coordinates

    """
    tuples_set = set()
    for sampled_adj in tqdm.tqdm(all_sampled_adj_freq):
        i_list = sampled_adj.nonzero()[0].tolist()
        j_list = sampled_adj.nonzero()[1].tolist()
        for i, j in zip(i_list,j_list):
            tuples_set.update([(i, j)])
    return list(tuples_set)

def get_cell_mean_sd(value,all_sampled_adj_freq):
    """
    
    Description
    -----------
    Compute mean and standard deviation

    Parameters
    ----------
    value : tuple
        coordinates to look for.
    all_sampled_adj_freq : list
        list of sampled adjacency matrices.

    Returns
    -------
    tuple
        coordinates, mean and sd across each sample.

    """
    count = []
    for sampled_adj in all_sampled_adj_freq:
        count.append(sampled_adj[value[0],value[1]])
    return value, np.mean(count), np.std(count)

def get_comb_mean_sd(path2,all_sampled_adj_freq,unique_values,var,focal_year):
    """
    

    Parameters
    ----------
    path2 : str
        path to load and save mean and sd adjacency matrix.
    all_sampled_adj_freq : list
        list of sampled adjacency matrices.
    unique_values : list
        list of unique coordinate to compute mean and sd.
    focal_year : int
        year of interest.

    Returns
    -------
    mean_comb : TYPE
        DESCRIPTION.
    sd_comb : TYPE
        DESCRIPTION.

    """
       
    mean_comb = lil_matrix(all_sampled_adj_freq[0].shape)
    sd_comb = lil_matrix(all_sampled_adj_freq[0].shape)
    
    # #mean_sd_list = [get_cell_mean_sd(value,all_sampled_adj_freq) for value in tqdm.tqdm(unique_values)]
    # print('get mean and sd')
    # mean_sd_list = Parallel(n_jobs= 20)(delayed(get_cell_mean_sd)(value,all_sampled_adj_freq)
    #                                     for value in tqdm.tqdm(unique_values))
    
    
    # row, col, mean, sd = [], [], [], []
    # for value, m, s in tqdm.tqdm(mean_sd_list):
    #     row.append(value[0])
    #     col.append(value[1])
    #     mean.append(m)
    #     sd.append(s)
        
    # mean_comb = sparse.coo_matrix((mean, (row, col)),
    #                               shape=all_sampled_adj_freq[0].shape)
    # sd_comb = sparse.coo_matrix((sd, (row, col)),
    #                               shape=all_sampled_adj_freq[0].shape)
    
    try:
        with open(path2 + "/iteration/mean_info_{}_{}.p".format('atypicality',focal_year),
              'rb') as f:
            mean_comb = pickle.load(f)
    except:
        mean_comb = lil_matrix(all_sampled_adj_freq[0].shape)
    
    try:
        with open(path2 + "/iteration/sd_info_{}_{}.p".format('atypicality',focal_year),
            'rb') as f:
            sd_comb = pickle.load(f)
    except:
        sd_comb = lil_matrix(all_sampled_adj_freq[0].shape)
    
   
    try:
        with open(path2 + "/iteration/mean_sd_last_i_{}_{}.txt".format('atypicality',focal_year),
              'r') as last_i:
            i = int(last_i.read())
    except:
        i = 0
    
    for value in tqdm.tqdm(unique_values[i:]):
        i+=1
        value, mean, sd = get_cell_mean_sd(value,all_sampled_adj_freq)
        mean_comb[value[0],value[1]] = mean
        sd_comb[value[0],value[1]] = sd
        if int(i)%1e7 == 0 :
            with open(path2 + "/iteration/mean_sd_last_i_{}_{}.txt".format('atypicality',focal_year),
                      'w') as last_i:
                last_i.write(str(i))
            pickle.dump(mean_comb, open(path2 + "/iteration/mean_info_{}_{}.p".format('atypicality',focal_year),
                                        "wb" ) )
            pickle.dump(sd_comb, open(path2 + "/iteration/sd_info_{}_{}.p".format('atypicality',focal_year),
                                        "wb" ) )
    return mean_comb, sd_comb


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
        

