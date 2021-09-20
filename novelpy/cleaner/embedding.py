import pymongo
import yaml
import spacy
import scispacy
import tqdm
import numpy as np
#import ast
from joblib import Parallel, delayed
import pandas as pd
from itertools import chain




class Embedding:
    
    def __init__(self,
                 client_name,
                 db_name,
                 collection_articles,
                 collection_authors,
                 var_year,
                 var_id,
                 var_pmid_list,
                 var_id_list,
                 var_auth_id,
                 pretrain_path,
                 var_title,
                 var_abstract,
                 var_keyword):
        """
        
        Description
        -----------
        Compute semantic centroid for each paper abstract and title, compute an author profil per year and
        add author profil from previous work for each article.

        Parameters
        ----------
        client_name : TYPE
            DESCRIPTION.
        db_name : TYPE
            DESCRIPTION.
        collection_articles : TYPE
            DESCRIPTION.
        collection_authors : TYPE
            DESCRIPTION.
        var_year : TYPE
            DESCRIPTION.
        var_id : TYPE
            DESCRIPTION.
        var_auth_id : TYPE
            DESCRIPTION.
        pretrain_path : TYPE
            DESCRIPTION.
        var_title : TYPE
            DESCRIPTION.
        var_abstract : TYPE
            DESCRIPTION.
        var_keyword : TYPE
            DESCRIPTION

        Returns
        -------
        None.

        """
        
        
        # Inheritant from dataset serai cool pierre just do it stp!
        
        self.client_name = client_name
        self.db_name = db_name
        self.collection_articles = collection_articles
        self.collection_authors = collection_authors
        self.var_year = var_year
        self.var_id = var_id
        self.var_pmid_list = var_pmid_list
        self.var_id_list = var_id_list
        self.var_auth_id = var_auth_id
        self.nlp = spacy.load(pretrain_path)
        self.var_title = var_title
        self.var_abstract = var_abstract
        self.var_keyword = var_keyword
        
        
        

        
    def get_articles_centroid(self,
                              pmid_start,
                              pmid_end,
                              chunk_size):
        """
        Description
        -----------
        Compute article centroid using a pretrain word emdedding model
        

        Parameters
        ----------
        pmid_start : int
            the first ID considered
        chunk_size : int
            how many articles will be loaded.

        Returns
        -------
        None.

        """
        for pmid in tqdm.tqdm(range(pmid_start,pmid_end,chunk_size)):
            client = pymongo.MongoClient(self.client_name)
            db = client[self.db_name]
            collection = db[self.collection_articles]
            pmids = np.arange(pmid,(pmid+chunk_size)).tolist()
            docs = collection.find({self.var_id:{'$in':pmids}})
            for doc in tqdm.tqdm(docs):
                # try:
                try:
                    tokens = self.nlp(doc[self.var_title])
                    article_title_centroid = np.sum([t.vector for t in tokens], axis=0) / len(tokens)
                    article_title_centroid = article_title_centroid.tolist()
                except:
                    pass
                
                if self.var_abstract in doc.keys() and doc[self.var_abstract] != "" :
                    # abstract = ast.literal_eval(doc[self.var_abstract])[0]['AbstractText']
                    abstract = doc[self.var_abstract][0]['AbstractText']
                    tokens = self.nlp(abstract)
                    article_abs_centroid = np.sum([t.vector for t in tokens], axis=0) / len(tokens)
                    article_abs_centroid = article_abs_centroid.tolist()
                else:
                    article_abs_centroid = None
                    
                collection.update_one({self.var_id:doc[self.var_id]},
                                      {'$set':{'title_embedding':article_title_centroid,
                                               'abstract_embedding':article_abs_centroid}})
                # except:
                #     pass
    
    
        
    
    def feed_author_profile(self,author_ids_list,n_jobs=1):
        """
        

        Parameters
        ----------
        author_ids_list : list
            list of author ids.
        n_jobs : int, optional
            Number of cores used for calculation. The default is 1.

        Returns
        -------
        None.

        """               
        
        def get_author_profile(and_id,
                              client_name,
                              db_name,
                              collection_articles,
                              collection_authors,
                              var_year,
                              var_id,
                              var_auth_id,
                              var_id_list,
                              var_keyword):
            """
            Description
            -----------
            This function calculate a semantic representation of previous work for a given author,
            for each year it calculate articles centroid semantic representation.
            Finaly it stores the author representation by year in mongo
        
            Parameters
            ----------
            and_id : int
                the id of the author
        
            """
        
            client = pymongo.MongoClient(client_name)
            db = client[db_name]
            collection_authors = db[collection_authors]
            collection_articles = db[collection_articles]
            doc = collection_authors.find({var_auth_id:and_id})[0]
            
            
            infos = list()
            for pmid in doc[var_id_list]:
                try:
                    article = collection_articles.find({var_id:pmid},no_cursor_timeout  = True)[0]
                    
                    year = article[var_year]
                    title = np.array(
                        article['title_embedding']
                        ) if article['title_embedding'] else None
                    abstract = np.array(
                        article['abstract_embedding']
                        ) if article['abstract_embedding'] else None
                    keywords = pd.DataFrame(article[var_keyword])['DescriptorName_UI'].to_list() # TO CHANGE FOR OTHER DB
                    infos.append({'year':year,
                                 'title':title,
                                 'abstract':abstract,
                                 'keywords':keywords})
                except:
                    pass
                
            df = pd.DataFrame(infos)
            if not df.empty:
                df = df[~df['year'].isin([''])]
                df['year'] = df['year'].astype(str)
                df_t = df[['year','title']].dropna()
                df_a = df[['year','abstract']].dropna()
                df_k = df[['year','keywords']].dropna()
                
                
                abs_year = df_a.groupby('year').abstract.apply(np.mean).to_dict()
                title_year =  df_t.groupby('year').title.apply(np.mean).to_dict()
                keywords_year =  df_k.groupby('year')['keywords'].apply(lambda x: list(set(chain.from_iterable(x)))).to_dict()
                
                if title_year:
                    for year in title_year:
                        title_year[year] = title_year[year].tolist()
                if abs_year:
                    for year in abs_year:
                        abs_year[year] = abs_year[year].tolist()
                
                
                collection_authors.update_one({var_auth_id:doc[var_auth_id]},
                                              {'$set':{'embedded_abs':abs_year,
                                                       'embedded_titles':title_year,
                                                       'keywords':keywords_year}})
                

        Parallel(n_jobs=n_jobs)(
            delayed(get_author_profile)(
                and_id,
                self.client_name,
                self.db_name,
                self.collection_articles,
                self.collection_authors,
                self.var_year,
                self.var_id,
                self.var_auth_id,
                self.var_id_list,
                self.var_keyword)
            for and_id in tqdm.tqdm(author_ids_list))
               
    
        
    def author_profile2papers(self,n_jobs=1):
        """
        

        Parameters
        ----------
        n_jobs : int, optional
            Number of cores used for calculation. The default is 1.

        Returns
        -------
        Store in mongo for each article the profile by year for each of the author (title, abstract, keywords)

        """
                
        def get_author_profile(doc,
                               var_id,
                               var_auth_id, 
                               var_year,
                               client_name,
                               db_name,
                               collection_articles,
                               collection_authors):
            """
            Internal to allow for parallel computing 

            """
            def drop_year_before_pub(dict_,year):
                dict_ = {key:dict_[key] for key in dict_ if key < year}
                return dict_
                
            client = pymongo.MongoClient(client_name)
            db = client[db_name]
            collection_authors = db[collection_authors]
            collection_articles = db[collection_articles]
            authors_profiles = list()
            current_year = doc[var_year]
            
            for auth in doc['a02_authorlist']: # TO CHANGE FOR OTHER DB
            
                profile = collection_authors.find({var_auth_id:auth['AID']})[0]
                abs_profile = profile['embedded_abs']
                title_profile = profile['embedded_titles']
                
                abs_profile = drop_year_before_pub(abs_profile,
                                                   current_year)
                
                title_profile = drop_year_before_pub(title_profile,
                                                     current_year)
                
                k_profile = drop_year_before_pub(profile['keywords'],
                                                 current_year)
                
                authors_profiles.append({var_auth_id : auth['AID'],
                                         'abs_profile' : abs_profile,
                                         'title_profile' :title_profile,
                                         'keywords_profile': k_profile})
                
            collection_articles.update_one({var_id:doc['var_id']},
                                           {'$set':{'authors_profiles':authors_profiles}})
        
        
        client = pymongo.MongoClient(self.client_name)
        db = client[self.db_name]
        collection = db[self.collection_articles]
        docs = collection.find()
        
        Parallel(n_jobs=n_jobs)(
            delayed(get_author_profile)(
                doc,
                self.var_id,
                self.var_auth_id, 
                self.var_year,
                self.client_name,
                self.db_name,
                self.collection_articles,
                self.collection_authors)
            for doc in tqdm.tqdm(docs))
        
    def get_references_embbeding(self,skip_,limit_,n_jobs=1):
        """
        

        Parameters
        ----------
        n_jobs : int, optional
            Number of cores used for calculation. The default is 1.

        Returns
        -------
        None.

        """
    
        def get_embedding_list(doc,
                               client_name,
                               db_name,
                               collection_articles,
                               var_id,
                               var_pmid_list):
            
            if var_pmid_list in doc.keys():
                client = pymongo.MongoClient(client_name)
                db = client[db_name]
                collection = db[collection_articles]
                
                refs = collection.find({var_id:{'$in':doc[var_pmid_list]}})
                
                refs_emb = []
                for ref in refs:
                    refs_emb.append({'id':ref[var_id],
                                     'abstract_embedding': ref['abstract_embedding'] if 'abstract_embedding' in ref.keys() else None,
                                     'title_embedding': ref['title_embedding'] if 'title_embedding' in ref.keys() else None})
                collection.update_one({var_id:doc[var_id]},
                                      {'$set':{'refs_embedding':refs_emb}})
                
                client.close()
            
            
        client = pymongo.MongoClient(self.client_name)
        db = client[self.db_name]
        collection = db[self.collection_articles]
         
        docs = collection.find().skip(skip_-1).limit(limit_)
        
        for doc in tqdm.tqdm(docs, total = limit_):
            get_embedding_list(
                doc,
                self.client_name,
                self.db_name,
                self.collection_articles,
                self.var_id,
                self.var_pmid_list)
        # Parallel(n_jobs=n_jobs)(
        #     delayed(get_embedding_list)(
        #         doc,
        #         self.client_name,
        #         self.db_name,
        #         self.collection_articles,
        #         self.var_id,
        #         self.var_pmid_list)
        #     for doc in tqdm.tqdm(docs))
            