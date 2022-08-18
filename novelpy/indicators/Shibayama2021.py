# inspired from https://github.com/DeyunYinWIPO/Novelty/blob/main/novelty_sci.py
import itertools
import numpy as np
from novelpy.utils.run_indicator_tools import Dataset
import pymongo
import tqdm
#from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import re 
from scipy.spatial.distance import cdist

def similarity_dist( i, j, distance_type):
    """
    Description
    -----------
    Compute a list of cosine similarity for all articles
    Parameters
    ----------
    n : int
        number of articles.
    doc_mat : np.array
        array of articles representation.
    Returns
    -------
    dist_list : list
        list of distances.
    """
    # Compute similarity
    cos_dist = cdist(np.array(i),np.array(j), metric=distance_type)
    n = cos_dist.shape[0]
    dist_list = []
    for i in range(n):
        for j in range(i+1,n):
            dist_list.append(cos_dist[i][j])
    return dist_list

def get_percentiles(dist_list):
    """
    Description
    -----------
    Return percentiles of the novelty distribution
    Parameters
    ----------
    dist_list : list
        list of distances.
    Returns
    -------
    nov_list : dict
        dict of novelty percentiles.
    """

    nov_list = {'percentiles': dict()}
    for q in [100, 99, 95, 90, 80, 50, 20, 10, 5, 1, 0]:
        nov_list['percentiles'].update({str(q)+'%': np.percentile(dist_list, q)})
    nov_list.update({'stats':{'mean': np.mean(dist_list),
                                'sd': np.std(dist_list),
                                'nb_comb' : len(dist_list)}})

    return nov_list

class Shibayama2021(Dataset):
    
    def __init__(self,
                 id_variable,
                 year_variable,
                 ref_variable, 
                 entity,
                 focal_year,
                 embedding_dim = 200,
                 client_name = None, 
                 db_name =  None,
                 collection_name = None,
                 collection_embedding_name = None,
                 distance_type = 'cosine',
                 density = False):
        """
        Description
        -----------
        Compute Shibayama et al (2021) novelty indicator and our alternative with author poximity

        Parameters
        ----------
        id_variable: str
            Name of the key which value give the identity of the document.
        year_variable : str
            Name of the key which value is the year of creation of the document.
        ref_variable : str
            Name of the key which value is the list of ids cited by the doc
        entity: list
            Which variable embedded to run the algorithm (e.g ["title","abstract"])
        focal_year: int
            Calculate the novelty score for every document which has a year_variable = focal_year.
        collection_name: str
            Name of the collection or the json file containing the variable.  
        collection_embedding_name: str
            Name of the collection or the json file containing the entity embedded.  
        client_name: str
            Mongo URI if your data is hosted on a MongoDB instead of a JSON file.
        db_name: str 
            Name of the MongoDB.
        distance_type : fun
            distance function, this function need to take an array with documents as row and features as columns, it needs to return a square matrix of distance between documents
        density: bool 
            If True, save an array where each cell is the score of a distance between a pair of document.
            If False, save only the percentiles of this array
        Returns
        -------
        None.

        """
        self.id_variable = id_variable
        self.ref_variable = ref_variable
        self.year_variable = year_variable
        self.entity = entity
        self.embedding_dim = embedding_dim
        self.distance_type = distance_type

        Dataset.__init__(
            self,
            client_name = client_name,
            db_name = db_name,
            collection_name = collection_name ,
            id_variable = id_variable,
            year_variable = year_variable,
            focal_year = focal_year,
            density = density)
        self.collection_embedding_name = collection_embedding_name
        self.path_score = "Result/shibayama/"
        if not os.path.exists(self.path_score):
            os.makedirs(self.path_score)
    
    
    def compute_score(self,refs,entity):
        """
        

        Parameters
        ----------
        doc : dict
            document from the embedded reference collection.
        entity : list
            'title_embedding' or 'abstract_embedding' or both.

        Returns
        -------
        None.

        """
        chunk_size = 10000
        for ent in entity:
            clean_refs = [ref for ref in refs if ref[ent] and isinstance(ref[ent],list)]
            n = len(clean_refs)
            if n > 1:
                doc_mat = []#np.zeros((n, self.embedding_dim))
                for i in range(n):
                    item = clean_refs[i][ent]
                    if item:
                        #doc_mat[i, :] =  item
                        doc_mat.append(item)
                dist_list = similarity_dist(i = doc_mat,j = doc_mat, distance_type = self.distance_type)
                nov_list = get_percentiles(dist_list)
                
                if self.client_name:
                    self.splitted_dict = []
                    if self.density:
                        if len(dist_list) > 10000:
                            list_chunked = [dist_list[i:i + chunk_size] for i in range(0, len(dist_list), chunk_size )]
                            for chunk in list_chunked:
                                new_dict = dict()
                                references_novelty = {
                                    'shibayama_{}'.format(ent) :nov_list,
                                    'scores_array_{}'.format(ent) :chunk
                                    }
                                new_dict.update(references_novelty)
                                self.splitted_dict.append(new_dict)
                        else:
                            new_dict = dict()
                            references_novelty = {
                                 'shibayama_{}'.format(ent) :nov_list,
                                 'scores_array_{}'.format(ent) : dist_list
                                 }
                            new_dict.update(references_novelty)                    
                            self.splitted_dict.append(new_dict)
                    else: 
                        new_dict = dict()
                        references_novelty = {
                             'shibayama_{}'.format(ent) :nov_list
                             }
                        new_dict.update(references_novelty)                    
                        self.splitted_dict.append(new_dict)
                    self.infos.update({ent:self.splitted_dict})
                else:
                    if self.density:
                        references_novelty = {
                            'shibayama_{}'.format(ent) :nov_list,
                            'scores_array_{}'.format(ent) :dist_list
                            }
                    else:
                        references_novelty = {
                            'shibayama_{}'.format(ent) :nov_list
                            }

                    self.infos.update(references_novelty)

    def get_references_embedding(self,
                                 doc):
        refs_embedding = []
        refs_ids = doc[self.ref_variable]
        for ref in refs_ids:
            if self.client_name:
                ref_embedding = self.collection_embedding.find_one({self.id_variable: ref})
            else:
                try:
                    ref_embedding = self.collection_embedding[ref]
                except:
                    continue
            if ref_embedding:
                if self.client_name:
                    ref_embedding.pop('_id')
                    ref_embedding.pop('year')
                refs_embedding.append(ref_embedding)
        return refs_embedding

    def load_data(self):

        if self.client_name:
            self.docs = self.collection.find({
                self.ref_variable:{'$ne':None},
                self.year_variable:self.focal_year
                },
                no_cursor_timeout=True)
            self.processed = []
            self.collection_embedding = self.db[self.collection_embedding_name]
        else:
            self.docs = json.load(open("Data/docs/{}/{}.json".format(self.collection_name,self.focal_year)))
            collection_embedding_acc = []
            all_years = [int(re.sub('.json','',file)) for file in os.listdir("Data/docs/{}/".format(self.collection_embedding_name))]
            for year in all_years:
                collection_embedding_acc += json.load(open("Data/docs/{}/{}.json".format(self.collection_embedding_name,year)))
            self.collection_embedding = {doc[self.id_variable]:{self.id_variable:doc[self.id_variable],
                                                           "title_embedding":doc["title_embedding"],
                                                           "abstract_embedding":doc["abstract_embedding"]} for doc in collection_embedding_acc}

    def get_indicator(self):

        self.load_data()
        print('Getting score per paper ...')     
        # Iterate over every docs 
        self.list_of_insertion = []

        for doc in tqdm.tqdm(self.docs):
            self.infos = dict()
            if doc[self.ref_variable] and len(doc[self.ref_variable])>1:
                #if doc[self.id_variable] in self.processed:
                #    continue
                #if self.client_name and len(doc[self.ref_variable]) == 500:
                #    docs_temp = self.collection.find({self.id_variable: doc[self.id_variable]})
                #    refs_emb = []
                #    for doc_temp in docs_temp:
                #        refs_emb.append(doc_temp[self.ref_variable])
                #    doc[self.ref_variable] = refs_emb 
                #    self.processed.append(doc[self.id_variable])
                refs = self.get_references_embedding(doc)
                self.compute_score(refs, self.entity)
                if self.client_name:
                    for ent in self.entity:
                        if ent in self.infos:
                            if self.infos[ent]:
                                for doc_to_insert in self.infos[ent]:
                                    scores = {self.id_variable: doc[self.id_variable],
                                            "year":doc["year"]}
                                    scores.update(doc_to_insert)
                                    self.list_of_insertion.append(scores)
                else:
                    if self.infos:
                        self.list_of_insertion.append({self.id_variable: doc[self.id_variable],'shibayama': self.infos})

        if self.client_name:
            if "output_shibayama" not in self.db.list_collection_names():
                print("Init output collection with index on id_variable ...")
                self.collection_output = self.db["output_shibayama"]
                self.collection_output.create_index([ (self.id_variable,1) ])
                self.collection_output.create_index([ (self.year_variable,1) ])
            else:
                self.collection_output = self.db["output_shibayama"]
            if self.list_of_insertion:
                self.collection_output.insert_many(self.list_of_insertion)
        else:
            if self.list_of_insertion:
                with open(self.path_score + "/{}.json".format(self.focal_year), 'w') as outfile:
                    json.dump(self.list_of_insertion, outfile)        
    


