import numpy as np
import pandas as pd
import networkx as nx
from novelpy.graphs.utils import * 
import yaml
import py2neo
import itertools
# Node format = list of list for ram usage


nodes = [
    [{"name":"node_1","ref":10},{"name":"node_2","ref":20}],
    [{"name":"node_3","ref":30},{"name":"node_4","ref":40}],
    ]

nodes_name = ["node_1","node_2","node_3","node_4"]

list_of_edges = {
    "2020" :[
        {"name_1":"node_1","name_2":"node_2","weight":4},
        {"name_1":"node_3","name_2":"node_2","weight":2},
        {"name_1":"node_1","name_2":"node_4","weight":10}
        ],
    "2010":[
        {"name_1":"node_1","name_2":"node_2","weight":4},
        {"name_1":"node_3","name_2":"node_2","weight":2},
        {"name_1":"node_1","name_2":"node_4","weight":10}        
        ]
    }


#Actual function test
with open("../mongo_config.yaml", "r") as infile:
    pars = yaml.safe_load(infile)['PC_Kevin']
    

URI = pars["neo4j_connection"]["URI"]
name = pars["neo4j_connection"]["auth"]["name"]
password = pars["neo4j_connection"]["auth"]["password"]
name_db = "TestYear"
inst = create_neo4j_year(name_db, URI, auth=(name,password))
inst.insert_nodes(nodes, index_field="name")
inst.insert_edges(list_of_edges)

# read test

graph = py2neo.Graph(URI, auth=(name,password), name=name_db)

query = """
MATCH (a:TestYear)-[r:`2000`]->(b:TestYear) 
RETURN a.name as source, b.name as target,r.weight as weight
"""
data = graph.run(query).to_data_frame()