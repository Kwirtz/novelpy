import os
import tqdm
import json
import pymongo 
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
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
            if self.entity_variable in doc.keys():
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
        




class get_stats():
        
    
    def __init__(self,
                 time_range,
                 year_variable,
                 client_name = None,
                 db_name = None):
        """
        

        Parameters
        ----------
        client_name : TYPE, optional
            DESCRIPTION. The default is None.
        db_name : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """
        
        self.time_range = time_range
        self.client_name = client_name
        self.db_name = db_name
        self.year_variable = year_variable
        
        if client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
        else:
            self.files_path = 'Data/docs'
         
        self.full_df = pd.DataFrame(columns = time_range)  
         
    def count_document(self, per_year = False):
        
        if per_year:
            if self.client_name:
                for coll in tqdm.tqdm(self.db.list_collection_names()):
                    counts = []
                    collection = self.db[coll]
                    for year in self.time_range:
                        counts.append(collection.count_documents({self.year_variable:year}))
                    # need to deal with authors db
                    if all(v == 0 for v in counts):
                        continue
                    self.full_df.loc[coll] = counts
            else:
                collections = os.listdir(self.files_path)
                for coll in tqdm.tqdm(collections):
                    counts = []
                    # need to deal with authors db
                    if coll.split(".")[-1] == "json":
                        continue
                    else:
                        for year in self.time_range:
                            counts.append(len(json.load(open(self.files_path + "/{}/{}.json".format(coll,year)))))
                    self.full_df.loc[coll] = counts
        else:
            counts = []
            
            if self.client_name:
                self.df_count = pd.DataFrame(columns = self.db.list_collection_names())
                for coll in tqdm.tqdm(self.db.list_collection_names()):
                    collection = self.db[coll]
                    counts.append(collection.count_documents({}))
            else:
                collections = os.listdir(self.files_path)
                self.df_count = pd.DataFrame(columns = collections)
                for coll in tqdm.tqdm(collections):
                    # need to deal with authors db
                    if coll.split(".")[-1] == "json":
                        docs = json.load(open(self.files_path + "/" + coll))
                        n = len(docs)
                    else:
                        n = 0
                        path_coll = self.files_path + "/" + coll
                        years = os.listdir(path_coll)
                        for year in years:
                            file = path_coll + "/" + year
                            docs = json.load(open(file))
                        n += len(docs)
                    counts.append(n)
                    
            self.df_count.loc["aggregate_count"] = counts
       
    def get_density_paper_per_author(self, collection_authors, author_id, list_name):
        
        if self.client_name:
            docs = self.db[collection_authors].find({})
        else:
            docs = json.load(open("Data/docs/{}.json".format(collection_authors)))
        self.n_papers = [len(doc[list_name]) for doc in tqdm.tqdm(docs)]
        self.n_papers_mean = np.mean(self.n_papers)
        extrem = np.percentile(self.n_papers,99)
        self.n_authors = len(self.n_papers)
        
        n_papers_plot = [n for n in self.n_papers if n<extrem]
        plt.figure()
        ax = sns.kdeplot(n_papers_plot, bw_adjust=5)
        ax.set_title('Density of co-authored papers for a given author')
        ax.set_xlabel('Number of papers')

    def get_density_reference_per_paper(self, collection_ref, references_variable, per_year = False):
        
        if per_year == False:
            if self.client_name:
                docs = self.db[collection_ref].find({})
            else:
                docs = []
                for year in self.time_range:
                    docs += json.load(open("Data/docs/{}/{}.json".format(collection_ref,year)))
            self.n_ref = [len(doc[references_variable]) for doc in tqdm.tqdm(docs)]
            self.n_ref_mean = np.mean(self.n_ref)
            self.n_ref_var = np.var(self.n_ref)
            extrem = np.percentile(self.n_ref,99)
            
            n_refs_plot = [n for n in self.n_ref if n<extrem]
            plt.figure()
            ax = sns.kdeplot(n_refs_plot, bw_adjust=5)
            ax.set_title('Density of cited papers for a given paper')
            ax.set_xlabel('Number of cited papers')
        else:
            n_ref_mean = []
            n_ref_var = []
            for year in self.time_range:
                if self.client_name:
                    docs = self.db[collection_ref].find({self.year_variable:year})
                else:
                    docs = json.load(open("Data/docs/{}/{}.json".format(collection_ref,year)))
                self.n_ref = [len(doc[references_variable]) for doc in tqdm.tqdm(docs)]
                n_ref_mean.append(np.mean(self.n_ref))
                n_ref_var.append(np.var(self.n_ref))                
            self.full_df.loc["mean_of_cited_paper"] = n_ref_mean
            self.full_df.loc["var_of_cited_paper"] = n_ref_var 
        

    def get_density_meshterms_per_paper(self, collection_meshterms, meshterms_variable, per_year = False):
        
        if per_year == False:
            if self.client_name:
                docs = self.db[collection_meshterms].find({})
            else:
                docs = []
                for year in self.time_range:
                    docs += json.load(open("Data/docs/{}/{}.json".format(collection_meshterms,year)))
            self.n_meshterms = [len(doc[meshterms_variable]) for doc in tqdm.tqdm(docs)]
            self.n_meshterms_mean = np.mean(self.n_meshterms)
            self.n_meshterms_var = np.var(self.n_meshterms)
            extrem = np.percentile(self.n_meshterms,99)
            
            n_meshterms_plot = [n for n in self.n_meshterms if n<extrem]
            plt.figure()
            ax = sns.kdeplot(n_meshterms_plot, bw_adjust=5)
            ax.set_title('Density of meshterms for a given paper')
            ax.set_xlabel('Number of meshterms papers')
        else:
            n_meshterms_mean = []
            n_meshterms_var = []
            for year in self.time_range:
                if self.client_name:
                    docs = self.db[collection_meshterms].find({self.year_variable:year})
                else:
                    docs = json.load(open("Data/docs/{}/{}.json".format(collection_meshterms,year)))
                self.n_meshterms = [len(doc[meshterms_variable]) for doc in tqdm.tqdm(docs)]
                n_meshterms_mean.append(np.mean(self.n_meshterms))
                n_meshterms_var.append(np.var(self.n_meshterms))                
            self.full_df.loc["mean_of_meshterms_per_paper"] = n_meshterms_mean
            self.full_df.loc["var_of_meshterms_per_paper"] = n_meshterms_var             
                 
    def get_stats_title_abs(self, collection_title_abs, title_key, abstract_key,per_year=False):
        
        
        if per_year:
            count_title = []
            count_abstract = []
            for year in self.time_range:
                if self.client_name:
                    count_title.append(self.db[collection_title_abs].count_documents({self.year_variable:year, title_key:{"$exists": True}}))
                    count_abstract.append(self.db[collection_title_abs].count_documents({self.year_variable:year, abstract_key:{"$exists": True}}))
                else:
                    docs = json.load(open("Data/docs/{}/{}.json".format(collection_title_abs,year)))
                    count_title.append(len([doc for doc in docs if title_key in doc]))
                    count_abstract.append(len([doc for doc in docs if abstract_key in doc]))
            
            self.full_df.loc["papers_with_title"] = count_title
            self.full_df.loc["papers_with_abstract"] = count_abstract 
        else:
            if self.client_name:
                docs = self.db[collection_title_abs].find({})
            else:
                docs = []
                for year in self.time_range:
                    docs += json.load(open("Data/docs/{}/{}.json".format(collection_title_abs,year)))
                self.count_title = len([doc for doc in docs if title_key in doc])
                self.count_abstract = len([doc for doc in docs if abstract_key in doc])
  
    
        