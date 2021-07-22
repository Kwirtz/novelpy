import pymongo
import yaml
import tqdm
from joblib import Parallel, delayed
from collections import defaultdict
import itertools
from scipy.sparse import lil_matrix
import numpy as np
import pickle
import os
from package.utils import create_cooc
 
with open("mongo_config.yaml", "r") as infile:
    pars = yaml.safe_load(infile)['PC_Kevin']
client_name = pars["pymongo_connection"]
URI = pars["neo4j_connection"]["URI"]
name = pars["neo4j_connection"]["auth"]["name"]
password = pars["neo4j_connection"]["auth"]["password"]

#%%
        
test = create_cooc(client_name = client_name, db_name = "pkg", collection_name = "articles",
                 var = "a02_authorlist", sub_var = "AID" )
test.main()

test2 = create_cooc(client_name = client_name, db_name = "pkg", collection_name = "articles",
                 var = "a03_keywordlist", sub_var = "Keyword" )
test2.main()

test3 = create_cooc(client_name = client_name, db_name = "pkg", collection_name = "articles",
                 var = "a14_referencelist", sub_var = "RefArticleId" )
test3.main()
