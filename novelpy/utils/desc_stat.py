import pandas as pd
import pymongo 
import tqdm
import os
import json

class Desc_stat:
        
    
    def __init__(self,
                 id_variable,
                 client_name = None,
                 db_name = None):
        """
        

        Parameters
        ----------
        id_variable : TYPE
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
        self.client_name = client_name
        self.db_name = db_name
    
    def create_entity_pub_list(self,
                               collection_articles,
                               entity_variable,
                               id_entity_variable):
        """
        

        Parameters
        ----------
        collection_articles : TYPE
            DESCRIPTION.
        entity_variable : TYPE
            DESCRIPTION.
        id_entity_variable : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """

        if self.client_name:
            self.client = pymongo.MongoClient(self.client_name)
            self.db = self.client[self.db_name]
            collection = self.db[collection_articles]
            docs = collection.find()
            pub_entity_list = []
            for doc in tqdm.tqdm(docs):
                pub_list = [pub[id_entity_variable] for pub in doc[entity_variable]]
                pub_entity_list.append({self.id_variable:doc[self.id_variable],
                                        '{}_list'.format(self.id_variable):pub_list})
        else:
            pub_entity_list = []
            files = os.listdir('Data/docs/{}'.format(collection_articles))
            for file in files:
                docs = json.load(open("Data/docs/{}/{}".format(collection_articles,file)))
                for doc in tqdm.tqdm(docs):
                    pub_list = [pub[id_entity_variable] for pub in doc[entity_variable]]
                    pub_entity_list.append({self.id_variable:doc[self.id_variable],
                                            '{}_list'.format(self.id_variable):pub_list})
        
        print('Get {} publication list...'.format(id_entity_variable))
        df = pd.DataFrame(pub_entity_list)
        edge_df = df.explode('{}_list'.format(self.id_variable))
        entity_pub_df = edge_df.groupby('{}_list'.format(self.id_variable))[self.id_variable].apply(list)
        entity_pub_df = entity_pub_df.reset_index()
        # for pkg : AID 0 is for authors without AID or Corporate author without identifier 
        if id_entity_variable == 'AID':
            entity_pub_df = entity_pub_df[entity_pub_df['{}_list'.format(self.id_variable)] != 0]
        
        if self.client_name:
            
            print('Export to mongo... ')
            entity_pub_df = entity_pub_df.to_dict('records')
            collection_entity = self.db["{}_{}".format(entity_variable,id_entity_variable)]
            collection_entity.create_index([ (id_entity_variable,1) ])
            
            collection_entity.insert_many(entity_pub_df)
        else:
            
            print('Export to json... ')
            entity_pub_df.to_json("Data/docs/{}_{}.json".format(entity_variable,id_entity_variable))
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        