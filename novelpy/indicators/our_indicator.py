import numpy as np
import tqdm
import itertools
import py2neo
import pickle
import os
from random import sample
from joblib import Parallel, delayed
from scipy.sparse import lil_matrix

class our_indicator:
    
    def __init__(self, g, n, year, B = 500, weighted = True, n_jobs = None, freq_method = "approx", resample = 0.99):
        
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
        self.B = B
        self.weighted = weighted
        self.n_jobs = n_jobs
        self.freq_method = freq_method
        self.resample = resample
        self.neo4j = {"URI":None, "auth":None}
        self.path = "paper/Results/our_novelty_non_normalized/"
        self.year = year
        if not os.path.exists(self.path):
            os.makedirs(self.path)
            
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
    
    def generate_freq_matrix(self):
        '''
        Description
        -----------
        
        Create an empty Df which will hold the frequency appearance of cooc of nodes in the random sample
        
        Parameters
        ----------

        Returns
        -------
        Adjacency matrix filled with 0, row/col length = number of nodes in the graph
        row/col labels = name of node

        '''
        
        df_freq = lil_matrix((self.n, self.n), dtype = np.int16)
        self.df_freq = df_freq
        
    def appearance_node(self):
        nodes = list(self.subgraph.nodes())
        nodes_cooc = itertools.combinations(nodes, r=2)
        if self.freq_method=="matrix":
            for cooc in nodes_cooc: 
                cooc = sorted(cooc)
                self.df_freq[str(cooc[0]), str(cooc[1])] += 1
        elif self.freq_method=="neo4j":
            for cooc in nodes_cooc:
                cooc = sorted(cooc)
                to_insert = {"Source":str(cooc[0]),"Target":str(cooc[1]),"Weight":1}
                self.list_of_insertion.append(to_insert)
                if len(self.list_of_insertion) > 10000:
                    self.neo4j_insert_edges()
        else:
            pass

    
    def neo4j_insert_edges(self):
        self.graph.run(self.transaction_edge, json=self.list_of_insertion)
        self.list_of_insertion = []

    def neo4j_create_index(self):
        query = """CREATE INDEX IF NOT EXISTS
        FOR (n:Items)
        ON (n.name)
        """
        self.graph.run(query)

    def neo4j_insert_nodes(self):
        dict_items = [{'name':str(name[0])} for name in self.g.nodes(data=True)]
        transaction = "UNWIND $json as data CREATE (n:Items) SET n = data"
        self.graph.run(transaction, json=dict_items)
    
    def neo4j_create_db(self):
        self.graph = py2neo.Graph(self.neo4j["URI"], auth=self.neo4j["auth"], name="neo4j")
        query = """ CREATE DATABASE {} IF NOT EXISTS""".format(self.neo4j["db_name"])
        self.graph.run(query)
        self.graph = py2neo.Graph(self.neo4j["URI"], auth=self.neo4j["auth"], name=self.neo4j["db_name"])
        self.graph.delete_all()
        self.neo4j_insert_nodes()
        self.neo4j_create_index()
    
    def get_random_sample(self):
        random_nodes = sample(list(self.g.nodes()), int(len(self.g)*self.resample))
        subgraph = self.g.subgraph(random_nodes)
        self.subgraph = subgraph

    def run_iteration(self):
        self.get_random_sample()
        if self.freq_method !="approx" :
            self.appearance_node()
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
        if self.freq_method == "matrix":
            self.generate_freq_matrix()
        elif self.freq_method == "neo4j":
            self.neo4j_create_db()
            self.list_of_insertion = []
            self.transaction_edge = """UNWIND $json as data
            MATCH (a:Items),(b:Items)
            WHERE a.name = data.Source AND b.name = data.Target
            MERGE (a)-[r:RELATION]->(b)
            ON CREATE
                SET r.n_collab = 1
            ON MATCH
                SET r.n_collab = r.n_collab + 1
            """
        print("Created !")
        
        if self.n_jobs == None:
            for it in tqdm.tqdm(range(self.B)):
                self.run_iteration() 
        else:
            Parallel(n_jobs=self.n_jobs,require="sharedmem")(delayed(self.run_iteration)() for i in tqdm.tqdm(range(self.B)))
        #self.compute_novelty()
        pickle.dump( self.resample, open( self.path + "/P_approx.p", "wb" ) )
        pickle.dump( self.B, open( self.path + "/B_simulation.p", "wb" ) )
        pickle.dump( self.df, open( self.path + "/{}.p".format(self.year), "wb" ) )