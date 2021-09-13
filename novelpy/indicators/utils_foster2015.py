#https://mapequation.github.io/infomap/python/infomap.html


import numpy as np
import os
from scipy.sparse import lil_matrix

class community_appartenance:
    
    def __init__(self, g, year, variable, community_algorithm):
        
        '''
        Description
        -----------
        Create our novelty score by computing the frequency of time they were in the same community
        
        Parameters
        ----------
        g : networkx graph
            The coocurence/adjacency matrix from the element we want to calculate the novelty score on.
        '''
        
        type_="<class 'networkx.classes.graph.Graph'>"
        if str(type(g)) != type_:
            raise ValueError("Invalid type_. Expected networkx graph")
        if g.is_directed == True:
            raise ValueError("Invalid graph. Expected graph to be undirected")
        self.g = g
        self.path = "Paper/Results/Foster2015/"
        self.year = year
        self.variable = variable
        self.community_algorithm = community_algorithm
        
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def run_iteration(self):
        if self.community_algorithm == "Louvain":
            self.Louvain_based()
        
    def generate_commu_adj_matrix(self):
        '''
        Description
        -----------
        
        Create an empty Df which will hold the novelty score later
        
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
        self.run_iteration()