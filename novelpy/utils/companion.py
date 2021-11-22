import numpy as np
from itertools import combinations
import tqdm
import pymongo
import pickle
import json
import os

class get_novelty_score:
    
    def __init__(self,
             entity_id,
             entity_year,
             variable,
             indicator,
             client_name = None,
             db_name = None):
        """
        Description
        -----------
        Class that returns the distribution of novelty scores for a given paper and for a list of indicator or variable
        
        Parameters
        ----------


        entity_id : int
            The id of the entity (paper/patent/others) you want to plot the distribution.
        entity_year : int
            The year of the entity (paper/patent/others) you want to plot the distribution.
        variable : str/list of str
            Plot the distribution for a specific unit of knowledge. 
            If arg is a list draw the different distribution on the same plot 
        indicator : str/ list of str
            Plot the distribution for a specific indicator.
            If arg is a list draw the different distribution on the same plot 
        client_name : str, optional
            client name. The default is None.
        db_name : str, optional
            db name. The default is None.    
            
        Returns
        -------
        None.
    
        """
        
        self.client_name = client_name
        self.db_name = db_name
        self.entity_id = entity_id
        self.entity_year = entity_year
        self.variable = variable
        self.indicator = indicator

        if self.client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db["output"]
        else:
            self.path_doc = "Result/{}/{}/{}".format(self.indicator, self.variable,self.year)

        
        
        def plot_dist(self):
    
    

class plot_dist:
    
    def __init__(self,
             entity_id = None,
             variable = None,
             indicator = None,
             client_name = None,
             db_name = None,
             collection_name = None):
        """
        Description
        -----------
        Class that returns the distribution of novelty scores for a given paper and for a list of indicator or variable
        
        Parameters
        ----------


        client_name : str, optional
            client name. The default is None.
        db_name : str, optional
            db name. The default is None.
        collection_name : str, optional
            collection name. The default is None.  
        client_name : str, optional
            client name. The default is None.
        db_name : str, optional
            db name. The default is None.
        collection_name : str, optional
            collection name. The default is None.        
            
        Returns
        -------
        None.
    
        """
        
        self.client_name = client_name
        self.db_name = db_name
        self.collection_name = collection_name
        self.id_variable = id_variable
        self.year_variable = year_variable
        self.variable = variable
        self.sub_variable = sub_variable
        self.focal_year = focal_year
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        self.new_infos = new_infos
        self.item_name = self.variable.split('_')[0] if self.variable else None
        
        if self.client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]

            
    def get_item_infos(self):
        """
   
        Description
        -----------        
        Get item info depedning on the indicator

        Parameters
        ----------
        item : dict
            item from a document list of items.
        indicator : str
            indicator for which the score is computed.

        Returns
        -------
        doc_item : dict/list
            dict or list depending on the indicator structured as needed for later usage.

        """
     
        if self.indicator == 'atypicality':
            if 'year' in item.keys():
                doc_item = {'item':item[self.sub_variable],
                                  'year':item['year']}
        elif self.indicator == 'kscores': 
            doc_item = item
        else:
            doc_item = item[self.sub_variable]
        
        return  doc_item
        
    

