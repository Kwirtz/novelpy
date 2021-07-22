import numpy as np
import pandas as pd
import tqdm
import py2neo

## TODO convert numpy/pandas edge_list adj and incidence

class network:
    
    def __init__(self, data, type_="adj",direction_ = "undir"):
        
        types = ["adj","inc","edge_list"]
        directions = ["undir","dir"]
        
        if type_ not in types:
            raise ValueError("Invalid type_. Expected one of: %s" % types)
        if direction_ not in directions:
            raise ValueError("Invalid direction_. Expected one of: %s" % directions)
        if not isinstance(data,(pd.core.series.Series,np.ndarray)):
            raise ValueError("Invalid type_. Expected a pandas dataframe or numpy array")
        
        if type_ != "adj":
            self.convert(data, type_, direction_)

    def convert(self, data, type_, direction_):
       
        if type_ == "inc":
            n = data.shape[0]
            data_temp = pd.DataFrame(np.zeros(n*n,dtype= "int8").reshape(n,n), dtype= "int8")
            if isinstance(data,np.ndarray):
                data = data.T
            for edge in data.T:
                if direction_ == "undir":
                    node1 = np.where(edge >= 1)[0][0]
                    node2 = np.where(edge >= 1)[0][1]
                    data_temp.at[node1,node2] += edge[node1]
                    data_temp.at[node2,node1] += edge[node2]
                elif direction_ == "dir":
                    node_from = np.where(edge < 0)[0][0]
                    node_to = np.where(edge > 0)[0][0]
                    data_temp.at[node_from,node_to] += edge[node_to]
                     
        if type_ == "edge_list":
            pass
        return data


# Random graph je sais pas si worth it de le faire nous même

class random:

    def erdos_renyi(self, n, p = 0.5, type_="undirected"):

        '''
        Description
        -----------
        Create a random graph following the second model of erdos-renyi procedure described in:
        https://en.wikipedia.org/wiki/Erd%C5%91s%E2%80%93R%C3%A9nyi_model
        
        Parameters
        ----------
        n : int
            number of vertices in the random graph.
        p : float
            probability to create an edge between two fixed entity. Default set at 0.5
        type : str
            Specify if the random graph is "directed" or "undirected". Default is undirected. If undirected is choosed
            we select the upper triangle from the directed one and repeat it twice.

        Returns
        -------
        adjacency matrix of the random graph

        '''
        
        types = ["undirected","directed"]
        if type_ not in types:
             raise ValueError("Invalid type_. Expected one of: %s" % types)
        if p > 1:
             raise ValueError("Invalid value of p. p is a probability so keep it <= 1")
        adj = np.random.binomial(1,p,n**2).reshape([n,n])
        
        if type_ == "undirected":
            upper = adj[np.triu_indices(n)]
            X = np.zeros((n,n))
            X[np.triu_indices(n)] = upper
            adj = X + X.T - np.diag(np.diag(X))
        
        return adj
    
    def barabasi_albert(self, m, n, c=1, p = 0.5, type_="undirected"):
        types = ["undirected","directed"]
        if type_ not in types:
             raise ValueError("Invalid type_. Expected one of: %s" % types)
        if p > 1:
             raise ValueError("Invalid value of p. p is a probability so keep it <= 1")
             
        condition = False
        while condition == False:
            data_init = pd.DataFrame(self.erdos_renyi(m))
            if len([row for row in data_init.iterrows() if row[1].sum()>=1]) == len(data_init):
                condition = True
        
        node_dict = {str(row[0]):int(row[1].sum()) for row in data_init.iterrows()}    
        list_existing = []
        for node in node_dict:
            for i in range(node_dict[node]):
                list_existing.append(node)
        
        data = np.zeros(n*n,dtype= "int8").reshape(n,n) 
        data[0:m,0:m] = data_init
        data = pd.DataFrame(data,dtype= "int8")

        for i in tqdm.tqdm(range(n-m)):
            n_to_connect = int(c)
            temp_list = list(list_existing)
            while n_to_connect>0:
                # choose uniformly a node to connect to the new
                node_to_connect = np.random.choice(list_existing)
                
                # update adjacency matrix

                data.at[int(node_to_connect),m+i ] = 1
                data.at[m+i,int(node_to_connect)] = 1               
                
                # update frequency table for next iteration of algorithm 
                list_existing.append(str(m+i))
                list_existing.append(str(node_to_connect))
                
                # update temp table so that already existing connection not done twice, 
                # TODO add option for multi link ? just remove this part
                temp_list = [node for node in temp_list if node not in [node_to_connect]]
                #-1 connection to do
                n_to_connect -= 1

        return(data)
    
    def watts_strogatz(self, n, k,beta = 0.5):
        data = pd.DataFrame(np.zeros(n*n,dtype= "int8").reshape(n,n), dtype= "int8")

        for row in data.iterrows():
            top_b = int(row[0]+(k/2))
            low_b = int(row[0]-(k/2))
            

            if low_b < 0:
                # all left neighbor = 1
                row[1][low_b:] = 1
                #all right neighbor = 1
                row[1][0:top_b+1] = 1
            elif top_b > (n-1):
                row[1][low_b:] = 1
                row[1][0:(top_b-n)+1] = 1
            else:
                row[1][low_b:top_b+1] = 1

        for row in data.iterrows():
            top_b = int(row[0]+(k/2))
            low_b = int(row[0]-(k/2))
            

            if low_b < 0:
                for index in row[1][int(row[0]):top_b+1].index:
                    # rewiring with prob beta
                    if np.random.binomial(1, beta) == 1:
                        # Rewire it to an other node (random uniform choice where value == 0 => no double edge self loops)
                        rewire_to = np.random.choice(row[1][row[1]==0].index)
                        data.at[row[0],index] = 0
                        data.at[index,row[0]] = 0
                        data.at[row[0],rewire_to] = 1
                        data.at[rewire_to,row[0]] = 1

            elif top_b > (n-1):
                for index in list(row[1][int(row[0]):].index) + list(row[1][0:(top_b-n)].index):
                    # rewiring with prob beta
                    if np.random.binomial(1, beta) == 1:
                        # Rewire it to an other node (random uniform choice where value == 0 => no double edge self loops)
                        rewire_to = np.random.choice(row[1][row[1]==0].index)
                        data.at[row[0],index] = 0
                        data.at[index,row[0]] = 0
                        data.at[row[0],rewire_to] = 1
                        data.at[rewire_to,row[0]] = 1

      
            else:
                for index in row[1][int(row[0]):top_b].index :
                    # rewiring with prob beta
                    if np.random.binomial(1, beta) == 1:
                        # Rewire it to an other node (random uniform choice where value == 0 => no double edge self loops)
                        rewire_to = np.random.choice(row[1][row[1]==0].index)
                        data.at[row[0],index] = 0
                        data.at[index,row[0]] = 0
                        data.at[row[0],rewire_to] = 1
                        data.at[rewire_to,row[0]] = 1


class create_neo4j_year:
    
    def __init__(self, name_db, URI, auth):
        self.name_db = name_db
        self.URI = URI
        self.auth = auth
    
    def insert_nodes(self, nodes, index_field = None):
        graph = py2neo.Graph(self.URI, auth=self.auth, name="system")
        graph.run("CREATE DATABASE %s IF NOT EXISTS" % (self.name_db))
        graph = py2neo.Graph(self.URI, auth=self.auth, name=self.name_db)
        graph.delete_all()
        transaction = "UNWIND $json as data CREATE (n:%s) SET n = data"%(self.name_db)
        print("Creating nodes ...|n")
        for chunck in tqdm.tqdm(nodes):
            graph.run(transaction, json=chunck)     
        print("|n Nodes created !")
        
        if index_field != None:
            query = """CREATE INDEX unique_id IF NOT EXISTS
            FOR (n:%s)
            ON (n.%s)
            """%(self.name_db,index_field)
            graph.run(query)
    
    def insert_edges(self,transaction_dict_year):
        graph = py2neo.Graph(self.URI, auth=self.auth, name=self.name_db)
        for year in transaction_dict_year:
            transaction = """UNWIND $json as data
            MATCH (a:%s),(b:%s)
            WHERE a.name = data.name_1 AND b.name = data.name_2
            MERGE (a)-[c:`%s`]->(b)
            ON CREATE
                SET c.weight = data.weight
            ON MATCH
                SET c.weight = c.weight + data.weight
            """%(self.name_db, self.name_db,int(year))
            if len(transaction_dict_year[year]) > 10000:
                transaction_list = []
                for i in transaction_dict_year[year]:
                    transaction_list.append(i)
                    if len(transaction_list) == 1000:
                        graph.run(transaction, json=transaction_list) 
                        transaction_list = []
                if transaction_list != []:
                    graph.run(transaction, json=transaction_list) 
            else: 
                graph.run(transaction, json=transaction_dict_year[year])  
                
                