import numpy as np
import pickle
import os
from random import sample
from scipy.sparse import lil_matrix
import bz2

class our_indicator:
    
    def __init__(self, g, n, year, variable, chunk, weighted = True, resample = 0.95):
        
        '''
        Description
        -----------
        Create our novelty score by computing the frequency of time they were in the same community
        
        Parameters
        ----------
        g : networkx graph
            The coocurence/adjacency matrix from the element we want to calculate the novelty score on.
        weighted : boolean
            If weighted or not
        n_jobs : int
            Number of cores
        freq_method: ["approx","matrix","neo4j"]
        '''
        
        type_="<class 'networkx.classes.graph.Graph'>"
        if str(type(g)) != type_:
            raise ValueError("Invalid type_. Expected networkx graph")
        if g.is_directed == True:
            raise ValueError("Invalid graph. Expected graph to be undirected")
        self.g = g 
        self.n = n
        self.chunk = chunk
        self.weighted = weighted
        self.resample = resample
        self.path = "./Results/our_novelty_non_normalized/"
        self.year = year
        self.variable = variable
        
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        if not os.path.exists(self.path+ str(self.variable) + "/" + str(self.year)):
            os.makedirs(self.path+ str(self.variable) + "/" + str(self.year))
        if not os.path.exists(self.path+ "{}/{}/subgraph_nodes".format(self.variable,self.year)):
            os.makedirs(self.path+ "{}/{}/subgraph_nodes".format(self.variable,self.year))

    def compute_novelty(self):
        '''
        Description
        -----------
        
        Create the novelty matrix
        
        Parameters
        ----------

        Returns
        -------

        '''
        if self.freq_method == "approx":
            cx = self.df.tocoo()
            for i,j in zip(cx.row, cx.col):
                self.df[i,j] = 1-(self.df[i,j]/(self.B*self.resample))
    
    def compressed_pickle(self, title, data):
        with bz2.BZ2File(title + ".pbz2", "w") as f: 
            pickle.dump(data, f)
        
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
        
        df = lil_matrix((self.n, self.n), dtype = np.int16)
        self.df = df

    def get_random_sample(self):
        random_nodes = sample(list(self.g.nodes()), int(len(self.g)*self.resample))
        subgraph = self.g.subgraph(random_nodes)
        subgraph_nodes = list(subgraph.nodes())
        pickle.dump(subgraph_nodes, open( self.path + "{}/{}/subgraph_nodes/{}.p".format(self.variable,self.year,self.i), "wb" ))
        self.subgraph = subgraph


    def run_iteration(self):
        self.get_random_sample()
        self.community_appartenance()
    
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
        for i in self.chunk:
            self.i = i
            self.run_iteration() 
        self.compressed_pickle(title = self.path + "{}/{}/{}".format(self.variable,int(self.year),self.i), data = self.df)
        #pickle.dump( self.df, open( self.path + "{}/{}/{}.p".format(self.variable,self.year,self.B), "wb" ))