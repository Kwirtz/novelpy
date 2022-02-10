import os
#import ast
import yaml
import tqdm
import json
import spacy
import pymongo
import scispacy
import numpy as np
import re
import pandas as pd
from itertools import chain
from pymongo import UpdateOne
from collections import defaultdict
from joblib import Parallel, delayed






class Embedding:
    
    def __init__(self,
                 year_variable,
                 time_range,
                 id_variable,
                 references_variable,
                 pretrain_path,
                 title_variable,
                 abstract_variable,
                 client_name = None,
                 db_name = None,
                 keywords_variable = None,
                 keywords_subvariable = None,
                 abstract_subvariable = None,
                 id_auth_variable = None,
                 auth_pubs_variable = None):
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
        self.time_range = time_range
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
        


    def init_dbs_centroid(self,
                 collection_articles,
                 collection_embedding):
        
        if self.client_name:
            self.all_years = self.db[collection_articles].distinct(self.year_variable) 
            if collection_embedding not in self.db.list_collection_names():
                print("Init embedding collection with index on id_variable ...")
                self.collection_embedding = self.db[collection_embedding]
                self.collection_embedding.create_index([ (self.id_variable,1) ])
            else:
                self.collection_embedding = self.db[collection_embedding]
        else:
            if not os.path.exists("Data/docs/{}".format(collection_embedding)):
                os.makedirs("Data/docs/{}".format(collection_embedding))
                # Get all years availables 
                self.all_years = [int(re.sub('.json','',file)) for file in os.listdir("Data/docs/{}/".format(collection_articles))]
   
    def load_data_centroid(self,
                  collection_articles,
                  year):
        
        if self.client_name:
            collection = self.db[collection_articles]
            self.docs = collection.find({self.year_variable:year},
                                   no_cursor_timeout = True)
        else:
            self.docs = json.load(
                open("Data/docs/{}/{}.json".format(collection_articles,
                                                   year)))
            
    def get_title_abs(self,
                      doc):
        ## Titles
        if (self.title_variable in doc.keys() and
            doc[self.title_variable] != "" ):
            
            tokens = self.nlp(doc[self.title_variable])
            article_title_centroid = np.sum([t.vector for t in tokens], axis=0) / len(tokens)
            self.article_title_centroid = article_title_centroid.tolist()
        else:
            self.article_title_centroid = None
        ## Abstracts
        if (self.abstract_variable in doc.keys() and
            doc[self.abstract_variable][0][self.abstract_subvariable] != "") :
            
            # abstract = ast.literal_eval(doc[self.abstract_variable])[0]['AbstractText']
            if self.abstract_subvariable:
                abstract = doc[self.abstract_variable][0][self.abstract_subvariable]
            else:
                abstract = doc[self.abstract_variable]
            tokens = self.nlp(abstract)
            article_abs_centroid = np.sum([t.vector for t in tokens], axis=0) / len(tokens)
            self.article_abs_centroid = article_abs_centroid.tolist()
        else:
            self.article_abs_centroid = None
        
    
    def insert_embedding_centroid(self,
                         doc):
        try:
            if self.client_name:
                self.list_of_insertion.append(
                    UpdateOne(
                        {self.id_variable : doc[self.id_variable]}, 
                        {'$set' : {
                            'year' : doc[self.year_variable],
                            'title_embedding' : self.article_title_centroid,
                            'abstract_embedding' : self.article_abs_centroid
                            }},
                        upsert = True)
                    )    
            ## Feed the db
                if len(self.list_of_insertion) % 1000 == 0:
                    self.collection_embedding.bulk_write(self.list_of_insertion)
                    self.list_of_insertion = []
    
            else: 
                self.list_of_insertion.append(
                    {self.id_variable : doc[self.id_variable],
                    'year' : doc[self.year_variable],
                    'title_embedding' : self.article_title_centroid,
                    'abstract_embedding' : self.article_abs_centroid
                    }
                    )
        except Exception as e:
            print(e)
        
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
        #Create folder or mongo database
        self.init_dbs_centroid(collection_articles,
                      collection_embedding)
        
        for year in tqdm.tqdm(self.all_years):
            self.load_data_centroid(collection_articles,
                           year)

            self.list_of_insertion = []
            
            for doc in tqdm.tqdm(self.docs):
                self.get_title_abs(doc)
                self.insert_embedding_centroid(doc)
                
               
            if self.client_name:
                self.collection_embedding.bulk_write(self.list_of_insertion)
            else: 
                with open("Data/docs/{}/{}.json".format(collection_embedding,year), 'w') as outfile:
                    json.dump(self.list_of_insertion, outfile)



################## REFERENCES ######################

    
    def load_data_refs(self,
                      collection_articles,
                      collection_embedding,
                      collection_ref_embedding):
            
        if self.client_name:
            if collection_ref_embedding not in self.db.list_collection_names():
                print("Init references embedding collection with index on id_variable ...")
                self.collection_ref_embedding = self.db[collection_ref_embedding]
                self.collection_ref_embedding.create_index([ (self.id_variable,1) ])
            else:
                self.collection_ref_embedding = self.db[collection_ref_embedding]

            self.collection_articles = self.db[collection_articles]
            self.collection_embedding = self.db[collection_embedding]
        else:
            collection_embedding_acc = []
            all_years = [int(re.sub('.json','',file)) for file in os.listdir("Data/docs/{}/".format(collection_embedding))]
            for year in all_years:
                collection_embedding_acc += json.load(open("Data/docs/{}/{}.json".format(collection_embedding,year)))
            self.collection_embedding = {doc[self.id_variable]:{self.id_variable:doc[self.id_variable],
                                                           "title_embedding":doc["title_embedding"],
                                                           "abstract_embedding":doc["abstract_embedding"]} for doc in collection_embedding_acc}  
            self.output_path = 'Data/docs/{}'.format(collection_ref_embedding)
            if not os.path.exists(self.out_path):
                os.makedirs(self.out_path)
                
    def get_embedding_list(self,
                           doc):
        
        refs_emb = []
        if self.references_variable in doc.keys():
            if self.client_name:
                refs = self.collection_embedding.find({
                    self.id_variable:{'$in':doc[self.references_variable]}
                    }
                    )
            else:
                #refs = []
                #refs = collection_embedding[collection_embedding[id_variable].isin(doc[self.references_variable])].to_dict('records')
                refs = [self.collection_embedding[id_] for id_ in doc["refs_pmid_wos"] if id_ in self.collection_embedding]
            for ref in refs:
                refs_emb.append({
                    'id':
                        ref[self.id_variable],
                    'abstract_embedding':
                        ref['abstract_embedding'] if 'abstract_embedding' in ref.keys() else None,
                    'title_embedding':
                        ref['title_embedding'] if 'title_embedding' in ref.keys() else None})
                
        self.infos = {'refs_embedding':refs_emb} if refs_emb else  {'refs_embedding': None}
       
    def insert_embedding_ref(self,
                             doc):
        
        if self.client_name:
            try:
                self.infos.update({self.year_variable:doc[self.year_variable]})
                self.list_of_insertion.append(UpdateOne({self.id_variable:doc[self.id_variable]},
                                                        {'$set': self.infos},
                                                        upsert = True))    
            except Exception as e:
                print(e)
            if len(self.list_of_insertion) % 1000 == 0:
                self.collection_ref_embedding.bulk_write(self.list_of_insertion)
                self.list_of_insertion = []
        else:
            try:
                self.infos.update({self.id_variable:doc[self.id_variable],
                            self.year_variable:doc[self.year_variable]})
                self.list_of_insertion.append(self.infos)    
            except Exception as e:
                print(e)

    def get_references_embedding(self,
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


        self.load_data_ref(collection_articles,
                       collection_embedding,
                       collection_ref_embedding)
            
        for year in self.time_range:

            if self.client_name:
                docs = collection_articles.find().skip(skip_-1).limit(limit_)
            else:
                docs = json.load(open("Data/docs/{}/{}.json".format(collection_articles,year)))

            self.list_of_insertion = []
            for doc in tqdm.tqdm(docs, total = limit_):
               self.get_embedding_list(doc)
               self.insert_embedding_ref(doc)

            if self.client_name:
                self.collection_ref_embedding.bulk_write(self.list_of_insertion)
            else:
                with open("{}/{}.json".format(self.out_path,year), 'w') as outfile:
                    json.dump(self.list_of_insertion, outfile)
            
        
        
        
        

################## AUTHORS ######################

    
    def drop_year_before_pub(dict_,year):
        dict_ = {key:dict_[key] for key in dict_ if int(key) < int(year)}
        return dict_
    
    def load_data_aut(self,
                      collection_authors,
                      collection_embedding,
                      skip_,
                      limit_):
        
        if self.client_name:
            if '{}_year_embedding'.format(self.id_auth_variable) not in self.db.list_collection_names():
                print("Init author year profile embedding collection with index on id_variable and year ...")
                self.collection_authors_years = self.db['{}_year_embedding'.format(self.id_auth_variable)]
                self.collection_authors_years.create_index([ (self.id_variable,1) ])
                self.collection_authors_years.create_index([ (self.year_variable,1) ])
            else:
                self.collection_authors_years = self.db['{}_year_embedding'.format(self.id_auth_variable)]
                        
                
            self.collection_authors = self.db[collection_authors]
            self.collection_embedding = self.db[collection_embedding]
            #collection_keywords = db[self.collection_keywords]
            self.authors = self.collection_authors.find({},no_cursor_timeout=True).skip(skip_-1).limit(limit_)
            self.embedding = None
        else:
            if not os.path.exists("Data/docs/authors_profiles/"):
                os.makedirs("Data/docs/authors_profiles")
                            
            self.authors = json.load(open("Data/docs/{}.json".format(collection_authors))) 
            all_years = [int(re.sub('.json','',file)) for file in os.listdir("Data/docs/{}/".format(collection_embedding))]
            self.embedding = pd.DataFrame()
            for year in all_years:
                self.embedding = pd.concat(
                    [
                     self.embedding,
                     pd.read_json("Data/docs/{}/{}.json".format(collection_embedding,year))
                     ]
                    )
            self.embedding.set_index(self.id_variable)
        
    def get_year_embedding(self,
                           df):
        
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
                
        infos = []
        for year in title_year:
            info = {
                'year':int(year),
                'embedded_abs':abs_year[year] if (abs_year and year in abs_year.keys()) else None,
                'embedded_titles':title_year[year] if (title_year and year in title_year.keys()) else None,
            #'keywords':keywords_year
            }
            infos.append(info)
        
        return infos
    
    def search_previous_work(self,
                             doc):
        
        if self.client_name:
            self.articles = self.collection_embedding.find({self.id_variable:{'$in':doc[self.auth_pubs_variable]}})
        else:
            try:
                self.articles = self.embedding[self.embedding[self.id_variable].isin(doc[self.auth_pubs_variable])].to_dict('records')
            except Exception as e:
                print(e)
                print(doc[self.auth_pubs_variable])
                self.articles = None
                
    def structure_previous_work(self,
                                article):
        
        if 'title_embedding' in article.keys():
        #try:
            year = article[self.year_variable]
            title = np.array(
                article['title_embedding']
                ) if article['title_embedding'] else None
            abstract = np.array(
                article['abstract_embedding']
                ) if article['abstract_embedding'] else None
            #keywords = pd.DataFrame(keyword[self.keywords_variable])[self.keywords_subvariable].to_list() # TO CHANGE FOR OTHER DB
            self.infos.append({'year':year,
                         'title':title,
                         'abstract':abstract,
                         #'keywords':keywords
                         })
        # except Exception as e:
        #     print(e)
        
    def get_author_profile(self,
                            doc):
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

        Returns
        -------
        infos : dict 
            title/abstract embedded representation and keyword list by year 


        """
        
        
        
        #keywords = collection_keywords.find({self.id_variable:{'$in':doc[self.auth_pubs_variable]}},no_cursor_timeout  = True)
        #for article, keyword in zip(articles,keywords) :
            
        self.search_previous_work(doc)
        
        self.infos = []
        if self.articles:
            for article in self.articles : 
                self.structure_previous_work(article)
                
            df = pd.DataFrame(self.infos)
            if not df.empty:
               self.infos = self.get_year_embedding(df)
               
               
    def insert_embedding_aut(self,
                             and_id):
        
        if self.client_name:
            if self.infos:
                for info in self.infos:
                    self.list_of_insertion.append(
                        UpdateOne(
                            {self.id_auth_variable : and_id},
                            {'$set': info},
                            upsert = True)
                        )    
            #except Exception as e:
            #    print(e)
            if len(self.list_of_insertion) % 1000 == 0:
                self.collection_authors_years.bulk_write(self.list_of_insertion)
                self.list_of_insertion = []
        else:
            if self.infos:
                for info in self.infos:
                    info.update({self.id_auth_variable : and_id})
                    
                    
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
                        
        
        self.load_data_aut(collection_authors,
                           collection_embedding,
                           skip_,
                           limit_)
        
        self.list_of_insertion = []
        for author in tqdm.tqdm(self.authors):
        #for and_id in tqdm.tqdm(author_ids_list):
            and_id = author[self.id_auth_variable]
            self.get_author_profile(doc = author)
            self.insert_embedding_aut(and_id)

        if self.list_of_insertion:
            if self.client_name:
                self.collection_authors.bulk_write(self.list_of_insertion)
            #else:
                #with open("Data/docs/authors_profiles.json", 'w') as outfile:
                #    json.dump(list_of_insertion, outfile)
    
    #########################################################################################
    #########################################################################################
    
    def load_data_profiles(self,
                          collection_articles,
                          collection_authors,
                          collection_articles_author_profile):
            
    
        if self.client_name:
            self.collection_articles = self.db[collection_articles]
            self.collection_authors = self.db[collection_authors]
            self.collection_articles_author_profile = self.db[collection_articles_author_profile]
        else:
            collection_authors = json.load(open("Data/docs/authors_profiles.json"))
            self.collection_authors = {author[self.id_auth_variable]: author for author in tqdm.tqdm(collection_authors)}
            self.out_path = 'Data/docs/{}'.format(collection_articles_author_profile)
            if not os.path.exists(self.out_path):
                os.makedirs(self.out_path)
    
    def get_current_author_profile(self,
                                   doc,
                                   session = None):
        """
        Get author profile from the authors collection, throwaway articles written after the focal publication
        Internal to allow for parallel computing latter

        Parameters
        ----------
        doc : dict
            document from the articles collection.
        Returns
        -------
        infos : dict
            DESCRIPTION.

        """
      
        authors_profiles = list()
        current_year = doc[self.year_variable]
        if 'a02_authorlist' in doc.keys():
            for auth in doc['a02_authorlist']: # TO CHANGE FOR OTHER DB
                if self.client_name:
                    profile = self.collection_authors.find_one({self.id_auth_variable:auth[self.id_auth_variable]})
                else:
                    profile = self.collection_authors[auth[self.id_auth_variable]]#collection_authors[id_auth_variable] == auth['AID']].to_dict('records')[0]
                try:
                    abs_profile = profile['embedded_abs']
                    abs_profile = self.drop_year_before_pub(abs_profile,
                                                       current_year)
                except:
                    abs_profile = None
                
                try:
                    title_profile = profile['embedded_titles']
                    title_profile = self.drop_year_before_pub(title_profile,
                                                         current_year)
                except:
                    title_profile = None
                    
                authors_profiles.append({self.id_auth_variable : auth['AID'],
                                         'abs_profile' : abs_profile,
                                         'title_profile' :title_profile,
                                         })
                # refresh because more than 30 min
                self.client.admin.command('refreshSessions', [session.session_id], session=session)

        self.infos = {'authors_profiles':authors_profiles} if authors_profiles else {'authors_profiles': None}
       
    def insert_embedding_paper(self,
                         doc):
        
        if self.client_name:
            try:
                self.infos.update({self.year_variable:doc[self.year_variable]})
                self.list_of_insertion.append(
                    UpdateOne(
                        {self.id_variable: doc[self.id_variable]},
                        {'$set': self.infos},
                        upsert = True)
                    )    
            except Exception as e:
                print(e)
            if len(self.list_of_insertion) % 1000 == 0:
                self.collection_articles_author_profile.bulk_write(self.list_of_insertion)
                self.list_of_insertion = []
        else:
            try:
                self.infos.update({self.id_variable: doc[self.id_variable],
                            self.year_variable:doc[self.year_variable]})
                self.list_of_insertion.append(self.infos)    
            except Exception as e:
                print(e)

    
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
                
        
        self.load_data_profiles(collection_articles,
                              collection_authors,
                              collection_articles_author_profile)
      
        for year in self.time_range:
            if self.client_name:
                session = self.client.start_session()
                docs = collection_articles.find({self.year_variable:year},no_cursor_timeout  = True, session=session).skip(skip_-1).limit(limit_)
            else:
                docs = json.load(open("Data/docs/{}/{}.json".format(collection_articles,year))) 
            
            self.list_of_insertion = []
            for doc in tqdm.tqdm(docs):
                self.get_current_author_profile(
                    doc = doc,
                    session = session
                    )
                self.insert_embedding_paper(doc)
                
            if self.client_name:
                self.collection_articles_author_profile.bulk_write(self.list_of_insertion)
            else:
                with open("{}/{}.json".format(self.out_path,year), 'w') as outfile:
                    json.dump(self.list_of_insertion, outfile)
  