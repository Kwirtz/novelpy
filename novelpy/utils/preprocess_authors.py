import json
import glob
import tqdm
import pickle
import pymongo
from collections import defaultdict



class create_authors_past():
    
    def __init__(self, collection_name, id_variable, 
                 variable, sub_variable, client_name = None, db_name = None):
        
        self.variable = variable
        self.sub_variable = sub_variable
        self.id_variable = id_variable        
        self.collection_name = collection_name
        self.client_name = client_name
        self.db_name = db_name
        if self.client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
            self.collection_new = self.db[self.collection_name+"_cleaned"]
            self.collection_new.create_index([ ("AID",1) ])
        else:
            self.files = glob.glob('Data/docs/{}/*.json'.format(self.collection_name))



        
    def author2paper(self):
        
        self.author2paper = defaultdict(list)
        if self.client_name:
            docs = self.collection.find({self.variable:{"$exists":1}})
            for doc in tqdm.tqdm(docs):
                for author in doc[self.variable]:
                    self.author2paper[author[self.sub_variable]].append(doc[self.id_variable])
        else:
            for file in self.files:
                with open(file, 'r') as f:
                    docs = json.load(f)
                for doc in tqdm.tqdm(docs):
                    for author in doc[self.variable]:
                        self.author2paper[author[self.sub_variable]].append(doc[self.id_variable])
        


    def update_db(self):
        
        list_of_insertion = []
        for author in tqdm.tqdm(self.author2paper):
            list_of_insertion.append({"AID":author,"doc_list":self.author2paper[author]})
            if self.client_name:
                if len(list_of_insertion) == 10000:
                        self.collection_new.insert_many(list_of_insertion)   
                        list_of_insertion = []
            else:
                continue
        if self.client_name:
             self.collection_new.insert_many(list_of_insertion)   
        else:
            with open('Data/docs/{}.json'.format(self.collection_name+"_cleaned"), 'w') as file:     
                        # A new file will be created
                json.dump(list_of_insertion, file)       
                  
