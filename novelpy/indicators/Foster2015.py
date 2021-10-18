#https://mapequation.github.io/infomap/python/infomap.html


import numpy as np
import os
from scipy.sparse import lil_matrix
import community as community_louvain
from collections import defaultdict
import itertools
import pickle
import networkx as nx
class Foster2015():
    
    
    def __init__(self, current_adj, year, variable, community_algorithm):
        
        '''
        Description
        -----------
        Create our novelty score by computing the frequency of time they were in the same community
        
        Parameters
        ----------
        g : networkx graph
            The coocurence/adjacency matrix from the element we want to calculate the novelty score on.
        '''
        

        self.g = nx.from_scipy_sparse_matrix(current_adj, edge_attribute='weight')
        type_="<class 'networkx.classes.graph.Graph'>"
        if str(type(self.g)) != type_:
            raise ValueError("Invalid type_. Expected networkx graph")
        if self.g.is_directed == True:
            raise ValueError("Invalid graph. Expected graph to be undirected")
        
        self.year = year
        self.variable = variable
        self.community_algorithm = community_algorithm
        self.path = "Data/score/foster/{}".format(self.variable)
        
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        
    def save_score_matrix(self):
        pickle.dump(self.df, open(self.path + "/{}.p".format(self.year),"wb" ) )
        
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
            for key, value in sorted(partition.items()):
                communities[value].append(key)
            for community in communities:
                community_appartenance = [i for i in itertools.combinations(communities[community], r=2)]
                for i in community_appartenance:
                    i = sorted(i)
                    self.df[i[0], i[1]] += 1

    def run_iteration(self):
        if self.community_algorithm == "Louvain":
            self.Louvain_based()

    def generate_commu_adj_matrix(self):
        '''
        Description
        -----------
        
        Create an empty Df which will hold the novelty score of the combination for the focal year
        
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
        
        Main analysis where we fill the commu_adj matrix
        
        Parameters
        ----------

        Returns
        -------
        Partition of the graph

        '''
        print("Create empty df ...")
        self.generate_commu_adj_matrix()
        print("Empty df created !")  
        print("Compute community and community appartenance for {}".format(self.year))
        self.run_iteration()
        print("Done !")
        self.save_score_matrix()