import pandas as pd
import pymongo 
import tqdm
import os
import json
from collections import defaultdict
class create_author_db():
        
    
    def __init__(self,
                 id_variable,
                 entity_variable,
                 id_entity_variable,
                 collection_authors,
                 client_name = None,
                 db_name = None):
        """
        

        Parameters
        ----------
        id_variable : TYPE
            DESCRIPTION.
        entity_variable : TYPE
            DESCRIPTION.
        id_entity_variable : TYPE
            DESCRIPTION.
        collection_authors : TYPE
            DESCRIPTION.
        client_name : TYPE, optional
            DESCRIPTION. The default is None.
        db_name : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        
        
        self.id_variable = id_variable
        self.entity_variable = entity_variable
        self.id_entity_variable = id_entity_variable
        self.collection_authors = collection_authors
        self.client_name = client_name
        self.db_name = db_name
        self.id2paper_list = defaultdict(list)

        self.create_entity_pub_list()

    def process_docs(self,docs):
        for doc in tqdm.tqdm(docs):
            pmid = doc[self.id_variable]
            authors = [author[self.id_entity_variable] for author in doc[self.entity_variable]]
            if self.id_entity_variable == 'AID':
                # for pkg : AID 0 is for authors without AID or Corporate author without identifier 
                [self.id2paper_list[id_].append(pmid) for id_ in authors if id_ != 0]
            else:
                [self.id2paper_list[id_].append(pmid) for id_ in authors]
    
    def create_entity_pub_list(self):
        """
        
        Parameters
        ----------


        Returns
        -------
        None.

        """

        if self.client_name:
            self.client = pymongo.MongoClient(self.client_name)
            self.db = self.client[self.db_name]
            collection = self.db[self.collection_authors]
            docs = collection.find()
            self.process_docs(docs)

        else:
            files = os.listdir('Data/docs/{}'.format(self.collection_authors))
            for file in files:
                docs = json.load(open("Data/docs/{}/{}".format(self.collection_authors,file)))
                self.process_docs(docs)
        
        list_of_insertion = [{self.id_entity_variable:author,"{}_list".format(self.id_variable):self.id2paper_list[author]} for author in self.id2paper_list]

        
        
        if self.client_name:
            
            print('Export to mongo... ')
            collection_entity = self.db["{}_{}".format(self.entity_variable,self.id_entity_variable)]
            collection_entity.create_index([ (self.id_entity_variable,1) ])
            collection_entity.insert_many(list_of_insertion)
        else:
            print('Export to json... ')
            with open("Data/docs/{}_{}.json".format(self.entity_variable,self.id_entity_variable),"w") as outfile:
                    json.dump(list_of_insertion, outfile)
        

        
        
        
        
        
        
        
        
        
        