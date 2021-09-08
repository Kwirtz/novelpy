import networkx as nx
import random

G=nx.gnm_random_graph(100,5)
for (u, v) in G.edges():
    G.edges[u,v]['weight'] = random.randint(0,10)
    
