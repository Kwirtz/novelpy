import os
import re
import tqdm
import pickle
import numpy as np
import pandas as pd
from random import sample
from sklearn import preprocessing
from itertools import combinations
from scipy.sparse import triu, lil_matrix
from novelpy.utils.run_indicator_tools import create_output

pd.options.mode.chained_assignment = None

def get_adjacency_matrix(unique_items,
                         items_list,
                         unique_pairwise,
                         keep_diag):
    """
    
    Description
    -----------
    Compute adjacency matrix for single and multiple document

    Parameters
    ----------
    unique_items : dict
        dict structured thi way name:index, file from the name2index.p generated with the cooccurrence matrices.
    items_list : list 
        list of list, each element of the list is the list of the item used
    unique_pairwise : bool
        to take into account multiple edges
    keep_diag : bool
        keep diagonal

    Returns
    -------
    adj_mat : scipy.sparse.csr.csr_matrix
        adjacency matrix in csr format

    """
    
    if unique_pairwise:     
        lb = preprocessing.MultiLabelBinarizer(classes=sorted(list(unique_items.keys())))
        dtm_mat = lil_matrix(lb.fit_transform(items_list))
        adj_mat = dtm_mat.T.dot(dtm_mat)
    else:
        adj_mat = lil_matrix((len(unique_items.keys()),len(unique_items.keys())), dtype = np.uint32)
        for item in items_list:
            for combi in list(combinations(item, r=2)):
                combi = sorted(combi)
                ind_1 = unique_items[combi[0]]
                ind_2 = unique_items[combi[1]]
                adj_mat[ind_1,ind_2] += 1
                if ind_1 != ind_2:
                    adj_mat[ind_2,ind_1] += 1          
    adj_mat = lil_matrix(adj_mat)
    if keep_diag == False:
        adj_mat.setdiag(0)
    adj_mat = adj_mat.tocsr()
    adj_mat = triu(adj_mat,format='csr')	
    adj_mat.eliminate_zeros()
    return adj_mat

def shuffle_network(current_items):
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
    return sorted(list(tuples_set))

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

def get_comb_mean_sd(path2,all_sampled_adj_freq,unique_values,variable,focal_year):
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
        with open(path2 + "/iteration/mean_info_{}_{}.p".format('uzzi',focal_year),
              'rb') as f:
            mean_comb = pickle.load(f)
    except:
        mean_comb = lil_matrix(all_sampled_adj_freq[0].shape)
    
    try:
        with open(path2 + "/iteration/sd_info_{}_{}.p".format('uzzi',focal_year),
            'rb') as f:
            sd_comb = pickle.load(f)
    except:
        sd_comb = lil_matrix(all_sampled_adj_freq[0].shape)
    
   
    try:
        with open(path2 + "/iteration/mean_sd_last_i_{}_{}.txt".format('uzzi',focal_year),
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
            with open(path2 + "/iteration/mean_sd_last_i_{}_{}.txt".format('uzzi',focal_year),
                      'w') as last_i:
                last_i.write(str(i))
            pickle.dump(mean_comb, open(path2 + "/iteration/mean_info_{}_{}.p".format('uzzi',focal_year),
                                        "wb" ) )
            pickle.dump(sd_comb, open(path2 + "/iteration/sd_info_{}_{}.p".format('uzzi',focal_year),
                                        "wb" ) )
    return mean_comb, sd_comb


class Uzzi2013(create_output):

    def __init__(self, 
             collection_name,
             id_variable,
             year_variable,
             variable,
             sub_variable,
             focal_year,                 
             client_name = None,
             db_name = None,
             nb_sample = 20,
             density = False,
             list_ids = None):
        """
        Description
        -----------
        Compute Atypicality as proposed by Uzzi, Mukherjee, Stringer and Jones (2013)
 
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
        nb_sample: int 
            Number of resample of the co-occurence matrix.
        density: bool 
            If True, save an array where each cell is the score of a combination. If False, save only the percentiles of this array

        Returns
        -------
        None.

        """

        self.nb_sample = nb_sample
        self.indicator = "uzzi"
        
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
        
        
        self.path_sample = "Data/cooc_sample/{}/".format(self.variable)
        self.path_score = "Data/score/uzzi/{}".format(self.variable)
        if not os.path.exists(self.path_sample):
            os.makedirs(self.path_sample)
        if not os.path.exists(self.path_score):
            os.makedirs(self.path_score)
        if not os.path.exists(self.path_score+"/iteration"):
            os.makedirs(self.path_score+"/iteration")

    def sample_network(self):
        """
        

        Parameters
        ----------
        nb_sample : int
            number of sample to create.

        Returns
        -------
        None.

        """
        already_computed = [
            f for f in os.listdir(self.path_sample) 
                             if re.match(r'sample_[0-9]+_{}'.format(self.focal_year), f)
                             ]

        for i in tqdm.tqdm(range(self.nb_sample),desc = 'Create sample network'):
            filename =  "sample_{}_{}.p".format(i,self.focal_year)
            if filename not in already_computed:
                # Shuffle Network
                sampled_current_items = shuffle_network(self.papers_items)
                # Get Adjacency matrix
                sampled_current_adj = get_adjacency_matrix(self.name2index,
                                                           sampled_current_items,
                                                           unique_pairwise = False,
                                                           keep_diag = True)
                pickle.dump(
                    sampled_current_adj,
                    open(self.path_sample + filename,
                         "wb" ) )

    def get_all_adj(self):
	# Get nb_sample networks
        self.all_sampled_adj_freq = []
        for i in tqdm.tqdm(range(self.nb_sample),desc = 'Get sample network'):
            sampled_current_adj_freq = pickle.load(
                open(self.path_sample + "sample_{}_{}.p".format(i,self.focal_year),
                "rb" ) )
            
            self.all_sampled_adj_freq.append(sampled_current_adj_freq)
        

                
    def compute_comb_score(self):
        """
               
        Description
        -----------
        Compute Atypicality Scores and store them on the disk

        Returns
        -------
        None.

        """
       	self.get_all_adj()
        self.unique_values = get_unique_value_used(self.all_sampled_adj_freq)
        
        mean_adj_freq, sd_adj_freq = get_comb_mean_sd(self.path_score,
                                                      self.all_sampled_adj_freq,
                                                      self.unique_values,
                                                      self.variable,
                                                      self.focal_year)
        
        comb_scores = (self.current_adj-mean_adj_freq)/sd_adj_freq  
        comb_scores[np.isinf(comb_scores)] =  None
        comb_scores[np.isnan(comb_scores)] =  None
        comb_scores = triu(comb_scores,format='csr')
        comb_scores.eliminate_zeros()
            
        pickle.dump(comb_scores,
                    open(self.path_score + "/{}.p".format(self.focal_year),"wb" ) )
        

    def get_indicator(self):
        self.get_data()
        print("Creating sample ...")
        self.sample_network()
        print("Sample created !")
        print('Getting score per year ...')  
        self.compute_comb_score()
        print("Matrice done !")  
        print('Getting score per paper ...')     
        self.update_paper_values()
        print("Done !")    
