import json
import glob
import tqdm
import pickle
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
            docs = self.collection.find({"refs_pmid_wos":{"$exists":1}})
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
        


    def update_db(self):
        
        if self.client_name:
            list_of_insertion = []
            docs = self.collection.find({"refs_pmid_wos":{"$exists":1}})
            for doc in tqdm.tqdm(docs):
                refs = doc[self.variable]
                cited_by = self.pmid2citedby[doc["PMID"]]
                list_of_insertion.append(pymongo.UpdateOne({self.id_variable: int(doc["PMID"])},
                                                           {'$set': {"citations": {"refs": refs,
                                                                                   "cited_by":cited_by}}},
                                                           upsert = False))
                if len(list_of_insertion) == 10000:
                    self.collection.bulk_write(list_of_insertion)
                    list_of_insertion = []
            self.collection.update_many({}, { "$unset" : { self.variable : 1} })
        else:
            gros_dict = {}
            for file in self.files:
                with open(file, 'r') as f:
                    docs = json.load(f)
                for doc in tqdm.tqdm(docs):
                    gros_dict[doc[self.id_variable]] = {}
                    gros_dict[doc[self.id_variable]] = {}
                    gros_dict[doc[self.id_variable]]["year"] = doc["year"]
                    gros_dict[doc[self.id_variable]]["citations"] = {}
                    gros_dict[doc[self.id_variable]]["citations"]["refs"] = doc[self.variable]
                    gros_dict[doc[self.id_variable]]["citations"]["cited_by"] = self.pmid2citedby[doc["PMID"]]
            with open('Data\docs\{}.pkl'.format(self.collection_name), 'wb') as file:     
                    # A new file will be created
                pickle.dump(gros_dict, file)       
              
"""
test = create_citation_network(client_name='mongodb://Pierre:ilovebeta67@localhost:27017/',db_name="novelty_final", collection_name = "Citation_network",
                               id_variable = "PMID", variable = "refs_pmid_wos")
"""

test = create_citation_network(collection_name = "Citation_network",
                               id_variable = "PMID", variable = "refs_pmid_wos")

test.pmid2citedby()
test.update_db()

