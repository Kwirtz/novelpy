import json
import glob
import tqdm
import pymongo
from collections import defaultdict



class create_citation_network():
    
    def __init__(self, collection_name, id_variable, 
                 variable, client_name = None, db_name = None):
        
        self.variable = variable
        self.id_variable = id_variable        
        self.collection_name = collection_name
        self.client_name = client_name
        self.db_name = db_name
        if self.client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
        else:
            self.files = glob.glob(r'Data\docs\{}\*.json'.format(self.collection_name))



        
    def pmid2citedby(self):
        
        self.pmid2citedby = defaultdict(list)
        if self.client_name:
            docs = self.collection.find()
            for doc in tqdm.tqdm(docs):
                for ref in doc[self.variable]:
                    self.pmid2citedby[ref].append(doc[self.id_variable])
        else:
            for file in self.files:
                with open(file, 'r') as f:
                    docs = json.load(f)
                for doc in tqdm.tqdm(docs):
                    for ref in doc[self.variable]:
                        self.pmid2citedby[ref].append(doc[self.id_variable])
        


    def update_db():
        pass


test = create_citation_network(collection_name = "Citation_net_sample", id_variable = "PMID",
                               variable = "refs_pmid_wos")
test.pmid2citedby()
df = test.pmid2citedby




pmid2citedby = defaultdict(list)
files = glob.glob(r'Data\docs\{}\*.json'.format("Citation_net_sample"))
for file in files:
    with open(file, 'r') as f:
        docs = json.load(f)
    for doc in tqdm.tqdm(docs):
        if doc["PMID"] == 14078174:
            print(yes )
        for ref in doc["refs_pmid_wos"]:
            pmid2citedby[ref].append(doc["PMID"])

set(pmid2citedby[ref])
