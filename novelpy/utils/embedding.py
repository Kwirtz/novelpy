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
import json
from pymongo import UpdateOne
import os



class Embedding:
    
    def __init__(self,
                 year_variable,
                 time_window,
                 id_variable,
                 references_variable,
                 auth_pubs_variable,
                 pretrain_path,
                 title_variable,
                 abstract_variable,
                 client_name = None,
                 db_name = None,
                 keywords_variable = None,
                 keywords_subvariable = None,
                 abstract_subvariable = None,
                 id_auth_variable = None):
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
        year_variable : str
            year variable name.
        id_variable : str
            identifier variable name.
        id_auth_variable : str
            authors identifer variable name.
        pretrain_path : str
            path to the pretrain word2vec: 'your/path/to/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0.
        title_variable : str
            title variable name.
        abstract_variable : str
            abstract variable name.
        keywords_variable : str
            keyword variable name.
        keywords_subvariable : str
            keyword subvariable name.

        Returns
        -------
        None.

        """
        
        
        # Inheritant from dataset serai cool 
        
        self.client_name = client_name
        self.db_name = db_name
        self.year_variable = year_variable
        self.time_window = time_window
        self.id_variable = id_variable
        self.references_variable = references_variable
        self.auth_pubs_variable = auth_pubs_variable
        self.id_auth_variable = id_auth_variable
        self.pretrain_path = pretrain_path
        self.title_variable = title_variable
        self.abstract_variable = abstract_variable
        self.keywords_variable = keywords_variable
        self.keywords_subvariable = keywords_subvariable
        self.abstract_subvariable = abstract_subvariable
        
        if self.client_name:
            self.client = pymongo.MongoClient(self.client_name)
            self.db = self.client[self.db_name]
        

        
    def get_articles_centroid(self,
                              collection_articles = None,
                              collection_embedding = None):
        """
        Description
        -----------
        Compute article centroid using a pretrain word emdedding model
        

        Parameters
        ----------

        Returns
        -------
        None.

        """
        self.nlp = spacy.load(self.pretrain_path)

        if self.client_name:
            if collection_embedding not in self.db.list_collection_names():
                    print("Init embedding collection with index on id_variable ...")
                    collection_embedding = self.db[collection_embedding]
                    collection_embedding.create_index([ (self.id_variable,1) ])
            else:
                collection_embedding = self.db[collection_embedding]


        if self.client_name:
                collection = self.db[collection_articles]
                docs = collection.find(no_cursor_timeout = True)
        else:
            docs = json.load(open("Data/docs/{}.json".format(collection_articles))) 

        list_of_insertion = []
        for doc in tqdm.tqdm(docs):
            # try:
            ## Titles
            if self.title_variable in doc.keys() and doc[self.title_variable] != "" :
                tokens = self.nlp(doc[self.title_variable])
                article_title_centroid = np.sum([t.vector for t in tokens], axis=0) / len(tokens)
                article_title_centroid = article_title_centroid.tolist()
            else:
                article_title_centroid = None
            ## Abstracts
            if self.abstract_variable in doc.keys() and doc[self.abstract_variable][0][self.abstract_subvariable] != "" :
                # abstract = ast.literal_eval(doc[self.abstract_variable])[0]['AbstractText']
                if self.abstract_subvariable:
                    abstract = doc[self.abstract_variable][0][self.abstract_subvariable]
                else:
                    abstract = doc[self.abstract_variable]
                tokens = self.nlp(abstract)
                article_abs_centroid = np.sum([t.vector for t in tokens], axis=0) / len(tokens)
                article_abs_centroid = article_abs_centroid.tolist()
            else:
                article_abs_centroid = None
            ## Feed the dict
            try:
                if self.client_name:
                    list_of_insertion.append(UpdateOne(
                        {
                        self.id_variable: doc[self.id_variable]}, 
                        {'$set':{
                                'year':doc[self.year_variable],
                                'title_embedding':article_title_centroid,
                                'abstract_embedding':article_abs_centroid
                                }}, upsert = True))    
                else: 
                    list_of_insertion.append(
                        {
                        self.id_variable: doc[self.id_variable],
                        'year':doc[self.year_variable],
                        'title_embedding':article_title_centroid,
                        'abstract_embedding':article_abs_centroid
                        })
            except Exception as e:
                print(e)
            ## Feed the db
            if len(list_of_insertion) % 1000 == 0:
                if self.client_name:
                    collection_embedding.bulk_write(list_of_insertion)
                    list_of_insertion = []

        if self.client_name:
            collection_embedding.bulk_write(list_of_insertion)
        else:
            with open("Data/docs/{}.json".format(collection_embedding), 'w') as outfile:
                json.dump(list_of_insertion, outfile)
        
        
    
    def feed_author_profile(self,
                            collection_authors,
                            collection_embedding,
                            skip_ = 1,
                            limit_ = 0):
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
                              year_variable,
                              id_variable,
                              id_auth_variable,
                              auth_pubs_variable,
                              keywords_variable,
                              keywords_subvariable,
                              collection_embedding,
                              collection_authors,
                              embedding,
                              client_name,
                              collection_keywords):
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
            year_variable : str
                name of the year variable.
            id_variable : str
                name of identifier variable.
            id_auth_variable : str
                name of the authors identifer.
            auth_pubs_variable : str
                list of id of artciles written by the author.
            keywords_variable : str
                keyword variable name.
            keywords_subvariable : str
                keyword subvariable name.

            Returns
            -------
            infos : dict 
                title/abstract embedded representation and keyword list by year 


            """
            
            
            
            infos = list()
            if client_name:
                articles = collection_embedding.find({id_variable:{'$in':doc[auth_pubs_variable]}})
            else:
                articles = embedding[embedding['PMID'].isin(doc[auth_pubs_variable])].to_dict('records')
            #keywords = collection_keywords.find({id_variable:{'$in':doc[auth_pubs_variable]}},no_cursor_timeout  = True)
            #for article, keyword in zip(articles,keywords) :
            for article in articles :
                if 'title_embedding' in article.keys():
                #try:
                    year = article[year_variable]
                    title = np.array(
                        article['title_embedding']
                        ) if article['title_embedding'] else None
                    abstract = np.array(
                        article['abstract_embedding']
                        ) if article['abstract_embedding'] else None
                    #keywords = pd.DataFrame(keyword[keywords_variable])[keywords_subvariable].to_list() # TO CHANGE FOR OTHER DB
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
                
        if self.client_name:
            collection_authors = self.db[collection_authors]
            collection_embedding = self.db[collection_embedding]
            #collection_keywords = db[self.collection_keywords]
            authors = collection_authors.find({}).skip(skip_-1).limit(limit_)
            embedding = None
        else:
            authors = json.load(open("Data/docs/{}.json".format(collection_authors))) 
            embedding = pd.read_json("Data/docs/{}.json".format(collection_embedding))

        # client = pymongo.MongoClient( client_name)
        # db = client[db_name]
        # collection_authors = db[collection_authors]
        # collection_embedding = db[collection_embedding]
        # collection_keywords = db[collection_keywords]
        list_of_insertion = []

        for author in tqdm.tqdm(authors):
        #for and_id in tqdm.tqdm(author_ids_list):
            and_id = author[self.id_auth_variable]
            infos = get_author_profile(
                doc = author,
                year_variable = self.year_variable,
                id_variable = self.id_variable,
                id_auth_variable = self.id_auth_variable,
                auth_pubs_variable = self.auth_pubs_variable,
                keywords_variable = self.keywords_variable,
                keywords_subvariable = self.keywords_subvariable,
                collection_embedding = collection_embedding,
                collection_authors = collection_authors,
                embedding = embedding,
                client_name = self.client_name,
                collection_keywords = None)

            if self.client_name:
                try:
                    list_of_insertion.append(UpdateOne({self.id_auth_variable : and_id}, {'$set': infos}, upsert = True))    
                except Exception as e:
                    print(e)
                if len(list_of_insertion) % 1000 == 0:
                    collection_authors.bulk_write(list_of_insertion)
                    list_of_insertion = []
            else:
                try:
                    infos.update({self.id_auth_variable : and_id})
                    list_of_insertion.append(infos)    
                except Exception as e:
                    print(e)

        if list_of_insertion:
            if self.client_name:
                collection_authors.bulk_write(list_of_insertion)
            else:
                with open("Data/docs/authors_profiles.json", 'w') as outfile:
                    json.dump(list_of_insertion, outfile)
        


        # Parallel(n_jobs=n_jobs)(
        #     delayed(get_author_profile)(
        #         and_id,
        #         self.client_name,
        #         self.db_name,
        #         self.collection_articles,
        #         self.collection_authors,
        #         self.year_variable,
        #         self.id_variable,
        #         self.id_auth_variable,
        #         self.auth_pubs_variable,
        #         self.keywords_variable)
        #     for and_id in tqdm.tqdm(author_ids_list))
                   
    
        
    def author_profile2papers(self,
                              collection_authors,
                              collection_articles,
                              collection_articles_author_profile,
                              skip_ = 1,
                              limit_ = 0):
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
                               id_variable,
                               id_auth_variable, 
                               year_variable,
                               collection_articles,
                               collection_authors,
                               client_name):
            """
            Get author profile from the authors collection, throwaway articles written after the focal publication
            Internal to allow for parallel computing latter

            Parameters
            ----------
            doc : dict
                document from the articles collection.
            id_variable : str
                name of identifier variable.
            id_auth_variable : str
                name of the authors identifer.
            year_variable : str
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
            current_year = doc[year_variable]
            if 'a02_authorlist' in doc.keys():
                for auth in doc['a02_authorlist']: # TO CHANGE FOR OTHER DB
                    if client_name:
                        profile = collection_authors.find_one({id_auth_variable:auth['AID']})
                    else:
                        profile = collection_authors[collection_authors[id_auth_variable] == auth['AID']].to_dict('records')[0]
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
                        
                    authors_profiles.append({id_auth_variable : auth['AID'],
                                             'abs_profile' : abs_profile,
                                             'title_profile' :title_profile,
                                             # 'keywords_profile': k_profile
                                             })
                    
            infos = {'authors_profiles':authors_profiles} if authors_profiles else {'authors_profiles': None}
            return infos
            

        out_path = 'Data/docs/{}'.format(collection_articles_author_profile)
        if not os.path.exists(out_path):
            os.makedirs(out_path)

        if self.client_name:
            collection_articles = self.db[collection_articles]
            collection_authors = self.db[collection_authors]
            collection_articles_author_profile = self.db[collection_articles_author_profile]
        else:
            collection_authors = pd.read_json("Data/docs/authors_profiles.json")

        for year in range(self.time_window[0],self.time_window[1]+1):
            if self.client_name:
                docs = collection_articles.find({self.year_variable:year}).skip(skip_-1).limit(limit_)
            else:
                docs = json.load(open("Data/docs/{}/{}.json".format(collection_articles,year))) 
         
                    
            # Parallel(n_jobs=n_jobs)(
            #     delayed(get_author_profile)(
            #         doc,
            #         self.id_variable,
            #         self.id_auth_variable, 
            #         self.year_variable,
            #         self.client_name,
            #         self.db_name,
            #         self.collection_articles,
            #         self.collection_authors)
            #     for doc in tqdm.tqdm(docs))
            
            list_of_insertion = []
            for doc in tqdm.tqdm(docs):
                infos = get_author_profile(
                    doc= doc,
                    id_variable = self.id_variable,
                    id_auth_variable = self.id_auth_variable, 
                    year_variable = self.year_variable,
                    collection_articles = collection_articles,
                    collection_authors = collection_authors,
                    client_name = self.client_name)
                if self.client_name:
                    try:
                        infos.update({self.year_variable:doc[self.year_variable]})
                        list_of_insertion.append(UpdateOne({self.id_variable: doc[self.id_variable]}, {'$set': infos}, upsert = True))    
                    except Exception as e:
                        print(e)
                    if len(list_of_insertion) % 1000 == 0:
                        collection_articles_author_profile.bulk_write(list_of_insertion)
                        list_of_insertion = []
                else:
                    try:
                        infos.update({self.id_variable: doc[self.id_variable],
                                    self.year_variable:doc[self.year_variable]})
                        list_of_insertion.append(infos)    
                    except Exception as e:
                        print(e)

            if self.client_name:
                collection_articles_author_profile.bulk_write(list_of_insertion)
            else:
                with open("{}/{}.json".format(out_path,year), 'w') as outfile:
                    json.dump(list_of_insertion, outfile)
            
        
        
    def get_references_embbeding(self,
                                collection_articles,
                                collection_embedding,
                                collection_ref_embedding,
                                skip_ = 1,
                                limit_ = 0):
        """
        Description
        -----------
        Store 

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
        def get_embedding_list(doc,
                               collection_embedding,
                               id_variable,
                               references_variable,
                               client_name):
            
            refs_emb = []
            if references_variable in doc.keys():
                if client_name:
                    refs = collection_embedding.find({id_variable:{'$in':doc[references_variable]}})
                else:
                    refs = collection_embedding[collection_embedding[id_variable].isin(doc[references_variable])].to_dict('records')

                for ref in refs:
                    refs_emb.append({'id':ref[id_variable],
                                     'abstract_embedding': ref['abstract_embedding'] if 'abstract_embedding' in ref.keys() else None,
                                     'title_embedding': ref['title_embedding'] if 'title_embedding' in ref.keys() else None})
            infos = {'refs_embedding':refs_emb} if refs_emb else  {'refs_embedding': None}
            return infos



        if self.client_name:
            if collection_ref_embedding not in self.db.list_collection_names():
                    print("Init references embedding collection with index on id_variable ...")
                    collection_ref_embedding = self.db[collection_ref_embedding]
                    collection_ref_embedding.create_index([ (self.id_variable,1) ])
            else:
                collection_ref_embedding = self.db[collection_ref_embedding]

            collection_articles = self.db[collection_articles]
            collection_embedding = self.db[collection_embedding]
        else:
            collection_embedding_name = collection_embedding[:]
            collection_embedding = pd.read_json("Data/docs/{}.json".format(collection_embedding_name))

        out_path = 'Data/docs/{}'.format(collection_ref_embedding)
        if not os.path.exists(out_path):
            os.makedirs(out_path)


        for year in range(self.time_window[0],self.time_window[1]+1):

            if self.client_name:
                docs = collection_articles.find().skip(skip_-1).limit(limit_)
            else:
                docs = json.load(open("Data/docs/{}/{}.json".format(collection_articles,year)))

            list_of_insertion = []
            for doc in tqdm.tqdm(docs, total = limit_):
                infos = get_embedding_list(
                    doc = doc,
                    collection_embedding = collection_embedding,
                    id_variable = self.id_variable,
                    references_variable = self.references_variable,
                    client_name = self.client_name)
                if self.client_name:
                    try:
                        infos.update({self.year_variable:doc[self.year_variable]})
                        list_of_insertion.append(UpdateOne({self.id_variable:doc[self.id_variable]}, {'$set': infos}, upsert = True))    
                    except Exception as e:
                        print(e)
                    if len(list_of_insertion) % 1000 == 0:
                        collection_ref_embedding.bulk_write(list_of_insertion)
                        list_of_insertion = []
                else:
                    try:
                        infos.update({self.id_variable:doc[self.id_variable],
                                    self.year_variable:doc[self.year_variable]})
                        list_of_insertion.append(infos)    
                    except Exception as e:
                        print(e)

            if self.client_name:
                collection_ref_embedding.bulk_write(list_of_insertion)
            else:
                with open("{}/{}.json".format(out_path,year), 'w') as outfile:
                    json.dump(list_of_insertion, outfile)
        # Parallel(n_jobs=n_jobs)(
        #     delayed(get_embedding_list)(
        #         doc,
        #         self.client_name,
        #         self.db_name,
        #         self.collection_articles,
        #         self.id_variable,
        #         self.references_variable)
        #     for doc in tqdm.tqdm(docs))
            