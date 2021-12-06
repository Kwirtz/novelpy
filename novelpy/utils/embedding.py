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
from pymongo import UpdateOne




class Embedding:
    
    def __init__(self,
                 client_name,
                 db_name,
                 collection_articles,
                 collection_authors,
                 collection_keywords,
                 collection_embedding,
                 var_year,
                 var_id,
                 var_pmid_list,
                 var_id_list,
                 var_auth_id,
                 pretrain_path,
                 var_title,
                 var_abstract,
                 var_keyword,
                 subvar_keyword):
        """
        
        Description
        -----------
        This class allows to 
        Compute semantic centroid for each paper (abstract and title)
        Compute an author profile of embedded articles per year 
        Add all authors previous work embedded representation for each article.

        Parameters
        ----------
        client_name : str
            mongo client name.
        db_name : str
            mongo db name.
        collection_articles : str
            mongo collection name for articles.
        collection_authors : str
            mongo collection name for authors.
        collection_keyword : pymongo.collection.Collection
            mongo collection for articles keywords.
        collection_embedding : pymongo.collection.Collection
            mongo collection for articles embedding.
        var_year : str
            year variable name.
        var_id : str
            identifier variable name.
        var_auth_id : str
            authors identifer variable name.
        pretrain_path : str
            path to the pretrain word2vec: 'your/path/to/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0.
        var_title : str
            title variable name.
        var_abstract : str
            abstract variable name.
        var_keyword : str
            keyword variable name.
        subvar_keyword : str
            keyword subvariable name.

        Returns
        -------
        None.

        """
        
        
        # Inheritant from dataset serai cool pierre just do it stp!
        
        self.client_name = client_name
        self.db_name = db_name
        self.collection_articles = collection_articles
        self.collection_authors = collection_authors
        self.collection_keywords = collection_keywords
        self.collection_embedding = collection_embedding
        self.var_year = var_year
        self.var_id = var_id
        self.var_pmid_list = var_pmid_list
        self.var_id_list = var_id_list
        self.var_auth_id = var_auth_id
        self.pretrain_path = pretrain_path
        self.var_title = var_title
        self.var_abstract = var_abstract
        self.var_keyword = var_keyword
        self.subvar_keyword = subvar_keyword
        
        
        

        
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
        self.nlp = spacy.load(self.pretrain_path)
        for pmid in tqdm.tqdm(range(pmid_start,pmid_end,chunk_size)):
            client = pymongo.MongoClient(self.client_name)
            db = client[self.db_name]
            collection = db[self.collection_articles]
            pmids = np.arange(pmid,(pmid+chunk_size)).tolist()
            docs = collection.find({self.var_id:{'$in':pmids}})
            list_of_insertion = []
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
                    
                try:
                    list_of_insertion.append(UpdateOne({
                        self.var_id: doc[self.var_id]}, 
                        {'$set':{'title_embedding':article_title_centroid,
                                               'abstract_embedding':article_abs_centroid}}, upsert = False))    
                except Exception as e:
                    print(e)
            collection.bulk_write(list_of_insertion)
            list_of_insertion = []
    
        
    
    def feed_author_profile(self,skip_,limit_):
        """
        Description
        -----------
        Store author profile in the authors collection

        Parameters
        ----------
        skip_ : int
            mongo skip argument.
        limit_ : int
            mongo limit argument.

        
        Returns
        -------
        None.

        """               
        
        def get_author_profile(doc,
                              collection_embedding,
                              collection_authors,
                              collection_keywords,
                              var_year,
                              var_id,
                              var_auth_id,
                              var_id_list,
                              var_keyword,
                              subvar_keyword):
            """
            Description
            -----------
            Track previous work for a given author, for each year it store all articles semantic
            representation in a dict

            Internal to allow for parallel computing latter
        
            Parameters
            ----------
            doc : dict
                document from the authors collection.
            collection_embedding : pymongo.collection.Collection
                mongo collection for articles embedding.
            collection_authors : pymongo.collection.Collection
                mongo collection for authors.
            collection_keywords : pymongo.collection.Collection
                mongo collection for keywords.
            var_year : str
                name of the year variable.
            var_id : str
                name of identifier variable.
            var_auth_id : str
                name of the authors identifer.
            var_id_list : str
                list of id of artciles written by the author.
            var_keyword : str
                keyword variable name.
            subvar_keyword : str
                keyword subvariable name.

            Returns
            -------
            infos : dict 
                title/abstract embedded representation and keyword list by year 


            """
            
            
            
            infos = list()
            articles = collection_embedding.find({var_id:{'$in':doc[var_id_list]}})
            #keywords = collection_keywords.find({var_id:{'$in':doc[var_id_list]}},no_cursor_timeout  = True)
            #for article, keyword in zip(articles,keywords) :
            for article in articles :
                if 'title_embedding' in article.keys():
                #try:
                    year = article[var_year]
                    title = np.array(
                        article['title_embedding']
                        ) if article['title_embedding'] else None
                    abstract = np.array(
                        article['abstract_embedding']
                        ) if article['abstract_embedding'] else None
                    #keywords = pd.DataFrame(keyword[var_keyword])[subvar_keyword].to_list() # TO CHANGE FOR OTHER DB
                    infos.append({'year':year,
                                 'title':title,
                                 'abstract':abstract,
                                 #'keywords':keywords
                                 })
                # except Exception as e:
                #     print(e)
                
            df = pd.DataFrame(infos)
            if not df.empty:
                df = df[~df['year'].isin([''])]
                df['year'] = df['year'].astype(str)
                df_t = df[['year','title']].dropna()
                df_a = df[['year','abstract']].dropna()
                #df_k = df[['year','keywords']].dropna()
                
                
                abs_year = df_a.groupby('year').abstract.apply(list).to_dict()
                title_year =  df_t.groupby('year').title.apply(list).to_dict()
                #keywords_year =  df_k.groupby('year')['keywords'].apply(list).to_dict()
                
                if title_year:
                    for year in title_year:
                        title_year[year] = [item.tolist() for item in title_year[year]]
                if abs_year:
                    for year in abs_year:
                        abs_year[year] = [item.tolist() for item in abs_year[year]]
                
                infos = {'embedded_abs':abs_year,
                'embedded_titles':title_year,
                #'keywords':keywords_year
                }
                return infos
                


        client = pymongo.MongoClient( self.client_name)
        db = client[self.db_name]
        collection_authors = db[self.collection_authors]
        collection_embedding = db[self.collection_embedding]
        collection_keywords = db[self.collection_keywords]

        # client = pymongo.MongoClient( client_name)
        # db = client[db_name]
        # collection_authors = db[collection_authors]
        # collection_embedding = db[collection_embedding]
        # collection_keywords = db[collection_keywords]
        authors = collection_authors.find({}).skip(skip_-1).limit(limit_)
        list_of_insertion = []

        for author in tqdm.tqdm(authors):
        #for and_id in tqdm.tqdm(author_ids_list):
            and_id = author[self.var_auth_id]
            infos = get_author_profile(
                author,
                collection_embedding,
                collection_authors,
                collection_keywords,
                self.var_year,
                self.var_id,
                self.var_auth_id,
                self.var_id_list,
                self.var_keyword,
                self.subvar_keyword)
            try:
                list_of_insertion.append(UpdateOne({self.var_auth_id : and_id}, {'$set': infos}, upsert = False))    
            except Exception as e:
                print(e)
            if len(list_of_insertion) % 1000 == 0:
                collection_authors.bulk_write(list_of_insertion)
                list_of_insertion = []
        if list_of_insertion:
            collection_authors.bulk_write(list_of_insertion)
        # Parallel(n_jobs=n_jobs)(
        #     delayed(get_author_profile)(
        #         and_id,
        #         self.client_name,
        #         self.db_name,
        #         self.collection_articles,
        #         self.collection_authors,
        #         self.var_year,
        #         self.var_id,
        #         self.var_auth_id,
        #         self.var_id_list,
        #         self.var_keyword)
        #     for and_id in tqdm.tqdm(author_ids_list))
                   
    
        
    def author_profile2papers(self,skip_,limit_):
        """
        Description
        -----------
        Store in mongo for each article the profile by year for each of the author (title, abstract, keywords)

        Parameters
        ----------
        skip_ : int
            mongo skip argument.
        limit_ : int
            mongo limit argument.

        
        Returns
        -------
        None.

        """        
                
        def get_author_profile(doc,
                               var_id,
                               var_auth_id, 
                               var_year,
                               collection_articles,
                               collection_authors):
            """
            Get author profile from the authors collection, throwaway articles written after the focal publication
            Internal to allow for parallel computing latter

            Parameters
            ----------
            doc : dict
                document from the articles collection.
            var_id : str
                name of identifier variable.
            var_auth_id : str
                name of the authors identifer.
            var_year : str
                name of the year variable.
            collection_articles : pymongo.collection.Collection
                mongo collection for articles.
            collection_authors : pymongo.collection.Collection
                mongo collection for authors.
            Returns
            -------
            infos : dict
                DESCRIPTION.

            """
            def drop_year_before_pub(dict_,year):
                dict_ = {key:dict_[key] for key in dict_ if int(key) < int(year)}
                return dict_
                
            authors_profiles = list()
            current_year = doc[var_year]
            if 'a02_authorlist' in doc.keys():
                for auth in doc['a02_authorlist']: # TO CHANGE FOR OTHER DB
                
                    profile = collection_authors.find_one({var_auth_id:auth['AID']})
                    
                    try:
                        abs_profile = profile['embedded_abs']
                        abs_profile = drop_year_before_pub(abs_profile,
                                                           current_year)
                    except:
                        abs_profile = None
                    
                    try:
                        title_profile = profile['embedded_titles']
                        title_profile = drop_year_before_pub(title_profile,
                                                             current_year)
                    except:
                        title_profile = None
                    
                    # try:
                    #     k_profile = drop_year_before_pub(profile['keywords'],
                    #                                      current_year)
                    # except:
                    #     k_profile = None 
                        
                    authors_profiles.append({var_auth_id : auth['AID'],
                                             'abs_profile' : abs_profile,
                                             'title_profile' :title_profile,
                                             # 'keywords_profile': k_profile
                                             })
                    
            infos = {'authors_profiles':authors_profiles} if authors_profiles else {'authors_profiles': None}
            return infos
            
                
            
                
        
        client = pymongo.MongoClient(self.client_name)
        db = client[self.db_name]
        collection_articles = db[self.collection_articles]
        collection_authors = db[self.collection_authors]
        docs = collection_articles.find({}).skip(skip_-1).limit(limit_)
        
        # Parallel(n_jobs=n_jobs)(
        #     delayed(get_author_profile)(
        #         doc,
        #         self.var_id,
        #         self.var_auth_id, 
        #         self.var_year,
        #         self.client_name,
        #         self.db_name,
        #         self.collection_articles,
        #         self.collection_authors)
        #     for doc in tqdm.tqdm(docs))
        
        list_of_insertion = []
        for doc in tqdm.tqdm(docs):
            infos = get_author_profile(
                doc,
                self.var_id,
                self.var_auth_id, 
                self.var_year,
                collection_articles,
                collection_authors)
            try:
                list_of_insertion.append(UpdateOne({self.var_id: doc[self.var_id]}, {'$set': infos}, upsert = False))    
            except Exception as e:
                print(e)
            if len(list_of_insertion) % 1000 == 0:
                collection_articles.bulk_write(list_of_insertion)
                list_of_insertion = []

        collection_articles.bulk_write(list_of_insertion)
            
        
        
    def get_references_embbeding(self,from_year,to_year,skip_,limit_):
        """
        Description
        -----------
        Store 

        Parameters
        ----------
        from_year : int
            First year to restrict the dataset.
        to_year : int
            Last year to restrict the dataset.
        skip_ : int
            mongo skip argument.
        limit_ : int
            mongo limit argument.

        Returns
        -------
        None.
        
        """
        def get_embedding_list(doc,
                               collection_embedding,
                               var_id,
                               var_pmid_list):
            
            refs_emb = []
            if var_pmid_list in doc.keys():

                refs = collection_embedding.find({var_id:{'$in':doc[var_pmid_list]}})
                
                for ref in refs:
                    refs_emb.append({'id':ref[var_id],
                                     'abstract_embedding': ref['abstract_embedding'] if 'abstract_embedding' in ref.keys() else None,
                                     'title_embedding': ref['title_embedding'] if 'title_embedding' in ref.keys() else None})
            infos = {'refs_embedding':refs_emb} if refs_emb else  {'refs_embedding': None}
            return infos
            
            
        client = pymongo.MongoClient(self.client_name)
        db = client[self.db_name]
        collection_articles = db[self.collection_articles]
        collection_embedding = db[self.collection_embedding]
         
        docs = collection_articles.find({self.var_year:{'$gte':from_year,'$lte':to_year}}).skip(skip_-1).limit(limit_)
        list_of_insertion = []
        for doc in tqdm.tqdm(docs, total = limit_):
            infos = get_embedding_list(
                doc,
                collection_articles,
                self.var_id,
                self.var_pmid_list)
            try:
                list_of_insertion.append(UpdateOne({self.var_id:doc[self.var_id]}, {'$set': infos}, upsert = False))    
            except Exception as e:
                print(e)
            if len(list_of_insertion) % 1000 == 0:
                collection_articles.bulk_write(list_of_insertion)
                list_of_insertion = []

        collection_articles.bulk_write(list_of_insertion)
        # Parallel(n_jobs=n_jobs)(
        #     delayed(get_embedding_list)(
        #         doc,
        #         self.client_name,
        #         self.db_name,
        #         self.collection_articles,
        #         self.var_id,
        #         self.var_pmid_list)
        #     for doc in tqdm.tqdm(docs))
            