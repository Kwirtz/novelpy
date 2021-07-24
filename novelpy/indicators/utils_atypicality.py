import pandas as pd
import pickle
from scipy.sparse import lil_matrix
from random import sample
from indicators.utils import *

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
