# inspired from https://github.com/DeyunYinWIPO/Novelty/blob/main/novelty_sci.py
import itertools
import numpy as np
from novelpy.utils.run_indicator_tools import Dataset
import pymongo
import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import json 
import os

def cosine_similarity_dist(n,doc_mat):
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
    cos_sim = cosine_similarity(doc_mat)
    dist_list = []
    for i in range(n):
        for j in range(i+1,n):
            dist_list.append(1 - cos_sim[i][j])

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

    nov_list = dict()
    for q in [100, 99, 95, 90, 80, 50, 20, 10, 5, 1, 0]:
        nov_list.update({str(q)+'%': np.percentile(dist_list, q)})

    return nov_list

class Author_proximity(Dataset):
    
    def __init__(self,
                 client_name = None, 
                 db_name =  None,
                 collection_name = None,
                 id_variable = None,
                 year_variable = None,
                 aut_profile_variable = None,
                 aut_id_variable = None,
                 entity = None,
                 focal_year = None,
                 windows_size = 5):
        """
        Description
        -----------
        Compute Author proximity as presented in Pelletier and Wirtz (2022)

        Parameters
        ----------
        id_variable : str
            identifier variable name.
        aut_profile_variable : str
            embedded representation of author articles variable name.
        aut_id_variable : str
            author id variable name.
        year_variable : str
            year variable name.
        entity : list
            Can be 'title_embedding' or 'abstract_embedding'
        focal_year : int
            Calculate novelty for object that have a creation/publication year = focal_year. 
        windows_size : int
            time window to consider to compute previous work representation 

        Returns
        -------
        None.

        """
        self.id_variable = id_variable
        self.aut_profile_variable = aut_profile_variable
        self.aut_id_variable = aut_id_variable
        self.year_variable = year_variable
        self.entity = entity
        self.windows_size = windows_size 

        Dataset.__init__(
            self,
            client_name = client_name,
            db_name = db_name,
            collection_name = collection_name ,
            id_variable = id_variable,
            year_variable = year_variable,
            focal_year = focal_year)
    

        self.path_score = "Data/score/Author_proximity/"
        if not os.path.exists(self.path_score):
            os.makedirs(self.path_score)
            
            
    def get_intra_dist(self,ent,doc):
        """
        

        Parameters
        ----------
        ent : str
            Entity used, can be title_profile or abstract_profile.
        doc : dict
            Treated document.

        Returns
        -------
        None.

        """
        self.focal_paper_id = doc[self.id_variable]
        nb_aut = len(doc[self.aut_profile_variable])
        self.intra_authors_dist = []
        self.authors_infos = []
        # save intra authors info
        self.authors_info_percentiles = {}

        for i in range(nb_aut):
            items = doc[self.aut_profile_variable][i][ent]
            aut_id = doc[self.aut_profile_variable][i][self.aut_id_variable]
            if items:
                aut_item = [items[key] for key in items if int(key) > (doc[self.year_variable]-self.windows_size) ]
                aut_item = list(itertools.chain.from_iterable(aut_item))
                aut_item = [item for item in aut_item if item]
                
                n = len(aut_item)
                if n >1:
                    self.authors_infos.append(aut_item)
                    aut_mat = np.zeros((n, 200))
                    for j in range(n):
                        aut_mat[j, :] = aut_item[j]
                    aut_dist = cosine_similarity_dist(n,aut_mat)
                    
                    self.authors_info_percentiles.update(
                        {
                            str(aut_id) : get_percentiles(aut_dist)
                            }
                        )
                    self.intra_authors_dist += aut_dist
                    
    def get_inter_dist(self):
        
        self.inter_authors_dist = []
        self.authors_infos_dist = {}
        # for all author
        for i in range(self.nb_aut):
            id_i = self.aut_ids[i]
            # for all other authors
            for j in range(i+1,self.nb_aut):
                temp_list = []
                id_j = self.aut_ids[j]
                # take each paper
                for item in self.authors_infos[i]:
                    # compare it with all papers of author j
                    for j_item in self.authors_infos[j]:
                        comb = np.array([item,j_item])
                        inter_paper_dist = cosine_similarity(comb)[0,1]
                        temp_list.append(inter_paper_dist)
                        self.inter_authors_dist.append(inter_paper_dist)
                        
                self.authors_infos_dist.update(
                    {
                        '{}_{}'.format(id_i,id_j) : get_percentiles(temp_list)
                        }
                    )
                

    def compute_score(self,doc,entity):
        """
        

        Parameters
        ----------
        doc : dict
            document from the embedded author collection.
        entity : str
            title or abstract.

        Returns
        -------
        None.

        """

        self.infos = dict()
        for ent in self.entity:

            self.get_intra_dist(ent,doc)

            if len(self.intra_authors_dist) > 0:
                intra_nov_list = get_percentiles(self.intra_authors_dist) 
                
                self.aut_ids = list(self.authors_info_percentiles.keys())    
                self.nb_aut = len(self.aut_ids)
                
                if self.nb_aut > 1:
                    self.get_inter_dist()
                    inter_nov_list = get_percentiles(self.inter_authors_dist)
                        
                    authors_novelty = {
                        'authors_novelty_{}_{}'.format(ent, str(self.windows_size)) :{
                            'intra':intra_nov_list,
                            'inter':inter_nov_list,
                            'scores_array_intra':self.intra_authors_dist,
                            'scores_array_inter':self.inter_authors_dist,
                            'individuals_scores': self.authors_info_percentiles,
                            'iter_individuals_scores':self.authors_infos_dist}
                        }
                    self.infos.update(authors_novelty)


    def get_indicator(self):
       
        if self.client_name:
            self.docs = self.collection.find({
                self.aut_profile_variable:{'$ne':None},
                self.year_variable:self.focal_year
                })
        else:
            self.docs = json.load(open("Data/docs/{}/{}.json".format(self.collection_name,self.focal_year)))
        # Iterate over every docs 
        list_of_insertion = []
        
        for doc in tqdm.tqdm(self.docs):
            if doc[self.aut_profile_variable]: 
                self.compute_score(doc, self.entity)
                
                if self.infos:
                    if self.client_name:
                        list_of_insertion.append(
                            pymongo.UpdateOne({self.id_variable: doc[self.id_variable]},
                                              {'$set': {'Author_proximity': self.infos}},
                                              upsert = True))
                    else:
                        list_of_insertion.append(
                            {
                                self.id_variable: doc[self.id_variable],'Author_proximity': self.infos
                                }
                            )
            
        if self.client_name:
            if "output" not in self.db.list_collection_names():
                print("Init output collection with index on id_variable ...")
                self.collection_output = self.db["output"]
                self.collection_output.create_index([ (self.id_variable,1) ])
            else:
                self.collection_output = self.db["output"]
            if list_of_insertion: 
                self.db['output'].bulk_write(list_of_insertion)
        else:
            if list_of_insertion:
                with open(self.path_score + "/{}.json".format(self.focal_year), 'w') as outfile:
                    json.dump(list_of_insertion, outfile)              
            


