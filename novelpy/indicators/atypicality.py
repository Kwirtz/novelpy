from .utils import *
import numpy as np

np.seterr(divide='ignore', invalid='ignore')

def Atypicality(true_current_adj,
                current_items,
                unique_items,
                nb_sample):
    
    # # Get the true frequency for each combinaison
    # true_current_adj_freq = get_comb_freq(true_current_adj)
    true_current_adj_freq = true_current_adj

    # Run nb_sample network shuffling, get the frequency of each combinaison for each sample 
    all_sampled_adj_freq = []
    for i in range(nb_sample):
        # Shuffle Network
        sampled_current_items = suffle_network(current_items)
        # Get Adjacency matrix
        sampled_current_adj = get_adjacency_matrix(unique_items,
                                                   sampled_current_items,
                                                   unique_pairwise = False,
                                                   keep_diag =True)
        # # Get frequency
        # sampled_current_adj_freq = get_comb_freq(sampled_current_adj)
        sampled_current_adj_freq = sampled_current_adj
        all_sampled_adj_freq.append(sampled_current_adj_freq.A)
        print('sampling '+str(i))
    samples_3d = np.dstack(all_sampled_adj_freq)
    mean_adj_freq = csr_matrix(np.mean(samples_3d,axis = 2))
    sd_adj_freq = csr_matrix(np.std(samples_3d,axis = 2))
    
    mean_adj_freq.eliminate_zeros()
    sd_adj_freq.eliminate_zeros()
    comb_scores = (true_current_adj_freq-mean_adj_freq)/sd_adj_freq  
    comb_scores[np.isinf(comb_scores)] =  0
    comb_scores[np.isnan(comb_scores)] =  0
    comb_scores = triu(comb_scores,format='csr')
    comb_scores.eliminate_zeros()
    
    return comb_scores
    
    
