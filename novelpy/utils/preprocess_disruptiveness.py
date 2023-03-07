import json
import glob
import tqdm
import pickle
import pymongo
from collections import defaultdict



class create_citation_network():
    
    def __init__(self, collection_name, id_variable, year_variable, 
                 variable, client_name = None, db_name = None):
        
        self.variable = variable
        self.id_variable = id_variable        
        self.collection_name = collection_name
        self.client_name = client_name
        self.db_name = db_name
        self.year_variable = year_variable
        if self.client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            self.collection_new = self.db[self.collection_name+"_cleaned"]
            self.collection_new.create_index([ (self.id_variable,1) ])
        else:
            self.files = glob.glob('Data/docs/{}/*.json'.format(self.collection_name))


        
    def id2citedby(self):
        
        self.pmid2citedby = defaultdict(list)
        if self.client_name:
            docs = self.collection.find({self.variable:{"$exists":1}})
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
            docs = self.collection.find({self.variable:{"$exists":1}})
            for doc in tqdm.tqdm(docs):
                refs = doc[self.variable]
                cited_by = self.pmid2citedby[doc[self.id_variable]]
                list_of_insertion.append({self.id_variable:doc[self.id_variable],
                                          self.year_variable:doc[self.year_variable],
                                          "citations": {"refs": refs,"cited_by":cited_by}})
                if len(list_of_insertion) == 1000:
                    self.collection_new.insert_many(list_of_insertion)
                    list_of_insertion = []
            self.collection_new.insert_many(list_of_insertion)
        else:
            gros_dict = {}
            for file in self.files:
                with open(file, 'r') as f:
                    docs = json.load(f)
                for doc in tqdm.tqdm(docs):
                    gros_dict[doc[self.id_variable]] = {}
                    gros_dict[doc[self.id_variable]][self.year_variable] = doc[self.year_variable]
                    gros_dict[doc[self.id_variable]]["citations"] = {}
                    gros_dict[doc[self.id_variable]]["citations"]["refs"] = doc[self.variable]
                    gros_dict[doc[self.id_variable]]["citations"]["cited_by"] = self.pmid2citedby[doc[self.id_variable]]
            with open('Data/docs/{}_cleaned.pkl'.format(self.collection_name), 'wb') as file:     
                    # A new file will be created
                pickle.dump(gros_dict, file)       
              
