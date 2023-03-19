#TODO https://mapequation.github.io/infomap/python/infomap.html


import os
import pickle
import itertools
import numpy as np
import networkx as nx
from packaging import version
from collections import defaultdict
from scipy.sparse import lil_matrix
import community as community_louvain
from novelpy.utils.run_indicator_tools import create_output



class Foster2015(create_output):
    
    
    def __init__(self,
             collection_name,
             id_variable,
             year_variable,
             variable,
             sub_variable,
             focal_year,
             starting_year = None,
             community_algorithm = "Louvain",
             client_name = None,
             db_name = None,
             density = False,
             list_ids = None):
        
        '''
        Description
        -----------
        Compute novelty as proposed by Foster, Rzhetsky, and Evans (2015)
        
        Parameters
        ----------
        
        
        collection_name: str
            Name of the collection or the json file containing the variable.  
        id_variable: str
            Name of the key which value give the identity of the document.
        year_variable: str
            Name of the key which value is the year of creation of the document.
        variable: str
            Name of the key that holds the variable of interest used in combinations.
        sub_variable: str
            Name of the key which holds the ID of the variable of interest.
        focal_year: int
            The year to start the accumulation of co-occurence matrices.
        starting_year: int
            The accumulation of co-occurence starting at year starting_year.
        client_name: str
            Mongo URI if your data is hosted on a MongoDB instead of a JSON file
        db_name: str
            Name of the MongoDB.
        community_algorithm: str
            The name of the community algorithm to be used.
        density: bool 
            If True, save an array where each cell is the score of a combination. If False, save only the percentile of this array

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
                               starting_year = starting_year,
                               density = density,
                               list_ids = list_ids)

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
                self.df[i[0], i[1]] = 1
        for i in range(len(self.g)):
            self.df[i, i] = 1
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
        
        self.df = lil_matrix((len(self.g), len(self.g)), dtype = np.int8)
        
    
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
        if version.parse(nx.__version__) < version.parse("3.0"):
            self.g = nx.from_scipy_sparse_matrix(self.current_adj, edge_attribute='weight') 
        else:
            self.g = nx.from_scipy_sparse_array(self.current_adj, edge_attribute='weight') 
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
