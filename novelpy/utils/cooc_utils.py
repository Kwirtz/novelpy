import pymongo
import tqdm
import itertools
from scipy.sparse import lil_matrix, csr_matrix
from sklearn import preprocessing
import numpy as np
import pickle
import os

class create_cooc:
    
    def __init__(self,
                 client_name,
                 db_name,
                 collection_name,
                 year_var,
                 time_window = range(1980,2020),
                 var = None,
                 sub_var = None,
                 weighted_network = False,
                 self_loop = False):
        '''
        Description
        -----------
        Create coocurences matrix of a field (e.g authors, keywords,ref) by year.
        Matrices are sparse csr and pickled for later usage
        
        Parameters
        ----------
        client_name : str
            name of the mongdb client
        db_name : str
            name of the db where your data is ("pkg" for us)
        collection_name : str
            name of the collection where the items yo data is ("pkg" for us)
        indicator : str
            indicator used the year is
        year_var : str
            field where the year is
        time_window: range
            range of year you will work on
        var : str
            field where the variable of interest is
        sub_var : str
            subfield where the variable of interest is
        weighted_network : bool
            allow a given document to make multiple time the same coocurrence
        self_loop : bool
            keep the diagonal on the coocurrence matrix
            
        '''
        self.client_name = client_name
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = pymongo.MongoClient(client_name)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.var = var
        self.sub_var = sub_var
        self.year_var = year_var
        self.time_window = time_window
        self.weighted_network = weighted_network
        self.self_loop = self_loop
        type1 = 'weighted_network' if self.weighted_network else 'unweighted_network'
        type2 = 'self_loop' if self.self_loop else 'no_self_loop'
        self.path = "Data/{}/{}_{}".format(var,type1,type2)
        if not os.path.exists(self.path):
            os.makedirs(self.path)
    
    """
    def item_list(self):
        '''
        Description
        -----------
        
        Create a set of the item of interests (e.g authors, keywords,ref)
        
        Parameters
        ----------

        Returns
        -------
        list of unique items

        ''' 
        final_list = []
        for year in tqdm.tqdm(self.time_window, desc="Get item list, loop on year"):
            item_list = []
            self.client = pymongo.MongoClient(self.client_name)
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            docs = self.collection.find({self.year_var:year},no_cursor_timeout=True)
            for doc in tqdm.tqdm(docs, desc="Get item list, loop on doc"):
                try:
                    items = doc[self.var]
                except:
                    continue
                items = [item[self.sub_var] for item in items]
                for item in items:
                    item_list.append(item)
            item_list = list(set(item_list))
            final_list += item_list
            final_list = list(set(final_list))
        self.item_list = sorted(final_list)
    """
        
    def item_list(self):
        '''
        Description
        -----------
        
        Create a set of the item of interests (e.g authors, keywords,ref)
        
        Parameters
        ----------

        Returns
        -------
        list of unique items

        ''' 
        final_list = []
        self.client = pymongo.MongoClient(self.client_name)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]
        docs = self.collection.find({},no_cursor_timeout=True)
        n_processed = 0
        for doc in tqdm.tqdm(docs, desc="Get item list, loop on every doc"):
            try:
                items = doc[self.var]
            except:
                continue
            items = [item[self.sub_var] for item in items]
            for item in items:
                final_list.append(item)
            n_processed += 1
            if n_processed % 10000 == 0:
                final_list = list(set(final_list))
        self.item_list = sorted(list(set(final_list)))

    def create_save_index(self):
        '''
        Description
        -----------
        
        Create dicts that transforms the name in the item_list to an index.
        Save the dicts to a pickle file.
        Necessary to work with a sparse matrix and update this matrix
        
        Parameters
        ----------

        Returns
        -------

        ''' 
        self.name2index = {name:index for name,index in zip(self.item_list, range(0,len(self.item_list),1))}
        self.index2name = {index:name for name,index in zip(self.item_list, range(0,len(self.item_list),1))}
        pickle.dump( self.name2index, open( self.path + "/name2index.p", "wb" ) )
        pickle.dump( self.index2name, open( self.path + "/index2name.p", "wb" ) )

    def create_matrix(self):
        '''
        Description
        -----------
        
        Create sparse matrix that will hold the coocurences of items in self.item_list
        Parameters
        ----------

        Returns
        -------
        sparse matrix

        ''' 
        self.x = lil_matrix((len(self.item_list), len(self.item_list)), dtype = np.int16)
        
        
    def populate_matrix(self,year):
        docs = self.collection.find({self.year_var:year}, no_cursor_timeout=True)
        
        if self.weighted_network:
            for doc in tqdm.tqdm(docs, desc = "Populate matrix"):
                try:
                    items = doc[self.var]
                except:
                    continue
                items = [item[self.sub_var] for item in items]
                for combi in list(itertools.combinations(items, r=2)):
                    combi = sorted(combi)
                    ind_1 = self.name2index[combi[0]]
                    ind_2 = self.name2index[combi[1]]
                    self.x[ind_1,ind_2] += 1
                    self.x[ind_2,ind_1] += 1
        else:
            docs_items = [set([item[self.sub_var] for item in doc[self.var]])
                          for doc in tqdm.tqdm(docs) if self.var in doc.keys()]
            lb = preprocessing.MultiLabelBinarizer(classes=self.item_list)
            dtm_mat = csr_matrix(lb.fit_transform(docs_items))
            self.x = lil_matrix(dtm_mat.T.dot(dtm_mat))
            
        if self.self_loop:
            self.x.setdiag(0)
            
    def save_matrix(self,year):
        '''
        Description
        -----------
        Convert the sparse lilmatrix to csr (easier to do 2000+2001)
        and save the sparse matrix to a pickle file
        
        Parameters
        ----------

        Returns
        -------

        ''' 
        self.x = self.x.tocsr()
        pickle.dump( self.x, open( self.path + "/{}.p".format(year), "wb" ) )
    
    def main(self):
        '''
        Description
        -----------
        
        Run all the function to save coocurence matrix (year by year) in a pickle file
        in a folder (depending on var name) with name2index and index2name
        Parameters
        ----------

        Returns
        -------

        ''' 
        self.item_list()
        self.create_save_index()
        for year in tqdm.tqdm(self.time_window, desc="For each year in range"):
            self.create_matrix()
            self.populate_matrix(year)
            self.save_matrix(year)
