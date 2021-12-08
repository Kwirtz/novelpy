#TODO https://mapequation.github.io/infomap/python/infomap.html


import os
import pickle
import itertools
import numpy as np
import networkx as nx
import community as community_louvain
from collections import defaultdict
from scipy.sparse import lil_matrix
from novelpy.utils.run_indicator_tools import create_output


class Foster2015(create_output):
    
    
    def __init__(self,
             collection_name,
             id_variable,
             year_variable,
             variable,
             sub_variable,
             focal_year,
             starting_year,
             community_algorithm = "Louvain",
             client_name = None,
             db_name = None):
        
        '''
        Description
        -----------
        Compute novelty as proposed by Foster, Rzhetsky, and Evans (2015)
        
        Parameters
        ----------
        current_adj : scipy.sparse.csr.csr_matrix
            The accumulated coocurence/adjacency matrix of items we want to calculate the novelty score on.
        focal_year : int
            Calculate novelty for object that have a creation/publication year = focal_year.
        variable : str
            Variable of interest (only for path purpose)
        community_algorithm : str
            The name of the community algorithm used (["Louvain"]).
        '''
        
        self.indicator = "foster"
        self.community_algorithm = community_algorithm
        
        create_output.__init__(self,
                               client_name = client_name,
                               db_name = db_name,
                               collection_name = collection_name ,
                               id_variable = id_variable,
                               year_variable = year_variable,
                               variable = variable,
                               sub_variable = sub_variable,
                               focal_year = focal_year,
                               starting_year = starting_year)

        self.path_score = "Data/score/foster/{}".format(self.variable)
        
        if not os.path.exists(self.path_score):
            os.makedirs(self.path_score)
        
    def save_score_matrix(self):
        pickle.dump(self.df, open(self.path_score + "/{}.p".format(self.focal_year),"wb" ) )
        
    def Louvain_based(self):
        '''
        Description
        -----------
        
        Add 1 in the adjacency matrix at the location of two nodes that were in the same community
        in the get_community function
        
        Parameters
        ----------

        Returns
        -------
        The Adjacency matrix

        '''
        print("Get Partition of community ...")
        partition = community_louvain.best_partition(self.g, partition=None, weight='weight', resolution=1.0, randomize=None, random_state=None)
        print("Partition Done !")
        communities = defaultdict(list)
        print("Updating the score matrix ...")
        for key, value in sorted(partition.items()):
            communities[value].append(key)
        for community in communities:
            community_appartenance = [i for i in itertools.combinations(communities[community], r=2)]
            for i in community_appartenance:
                i = sorted(i)
                self.df[i[0], i[1]] += 1
        print("Done ...")
    def run_iteration(self):
        if self.community_algorithm == "Louvain":
            self.Louvain_based()

    def generate_commu_adj_matrix(self):
        '''
        Description
        -----------
        
        Create an empty matrix which will hold the novelty score of the combination (i,j) for the focal year
        
        Parameters
        ----------

        Returns
        -------
        Adjacency matrix filled with 0, row/col length = number of nodes in the graph
        row/col labels = name of node

        '''
        
        df = lil_matrix((len(self.g), len(self.g)), dtype = np.int8)
        self.df = df
    
    
    def get_indicator(self):
        '''
        Description
        -----------
        
        Main analysis where we fill an adjacency matrix with element (i,j). (i,j) = 0 if i and j are in the same community
        else 1
        
        Parameters
        ----------

        Returns
        -------
        None

        '''
        self.get_data()
        self.g = nx.from_scipy_sparse_matrix(self.current_adj, edge_attribute='weight')         
        print("Create empty df ...")
        self.generate_commu_adj_matrix()
        print("Empty df created !")  
        print("Compute community and community appartenance for {}".format(self.focal_year))
        self.run_iteration()
        print("Done !")
        print("Saving score matrix ...")
        self.save_score_matrix()
        print("Saved ...")
        print('Getting score per paper ...')        
        self.update_paper_values()
        print("Done !")