# inspired from https://github.com/DeyunYinWIPO/Novelty/blob/main/novelty_sci.py
import itertools
import numpy as np
from novelpy.utils.run_indicator_tools import Dataset
import pymongo
from pymongo import UpdateOne
import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import json
import os
import bson
import math
from scipy.spatial.distance import cdist
import pandas as pd

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
    if i == j:
        n = cos_dist.shape[0]
        dist_list = []
        for i in range(n):
            for j in range(i+1,n):
                dist_list.append(cos_dist[i][j])
    else:
        dist_list = [num for line in cos_dist.tolist() for num in line]

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


def intra_cosine_similarity(items,
                            n,
                            distance_type):
    
    aut_mat = [] #np.zeros((n, len(items[0])))
    for j in range(n):
        aut_mat.append(items[j])#[j, :] = items[j]
    aut_dist = similarity_dist( i = aut_mat, j = aut_mat, distance_type = distance_type)
    
    return aut_dist

class Author_proximity(Dataset):
    
    def __init__(self,
                 client_name = None, 
                 db_name =  None,
                 collection_name = None,
                 id_variable = None,
                 year_variable = None,
                 aut_list_variable = None,
                 aut_id_variable = None,
                 entity = None,
                 focal_year = None,
                 windows_size = 5,
                 density = False,
                 distance_type = 'cosine'):
        """
        Description
        -----------
        Compute Author proximity as presented in Pelletier and Wirtz (2022)

    
        Parameters
        ----------
        client_name : TYPE, optional
            DESCRIPTION. The default is None.
        db_name : TYPE, optional
            DESCRIPTION. The default is None.
        collection_name : TYPE, optional
            DESCRIPTION. The default is None.
        id_variable : str
            identifier variable name.
        aut_list_variable : str
            list of authors variable name.
        aut_id_variable : str
            author id variable name.
        year_variable : str
            year variable name.
        entity : list
            Can be 'title' or/and 'abstract'
        focal_year : int
            Calculate novelty for object that have a creation/publication year = focal_year. 
        windows_size : int
            time window to consider to compute previous work representation 


        Returns
        -------
        None.

        """
        self.id_variable = id_variable
        self.aut_list_variable = aut_list_variable
        self.aut_id_variable = aut_id_variable
        self.year_variable = year_variable
        self.entity = entity
        self.windows_size = windows_size 
        self.distance_type = distance_type
        self.output_name = 'output_Author_proximity'
        Dataset.__init__(
            self,
            client_name = client_name,
            db_name = db_name,
            collection_name = collection_name ,
            id_variable = id_variable,
            year_variable = year_variable,
            focal_year = focal_year,
            density = density)
        if self.client_name:
            self.collection_authors_years = self.db['AID_year_embedding'] 
        else:
            self.collection_authors_years = pd.read_json("Data/docs/AID_year_embedding.json")
        self.path_output = "Data/Result/Author_proximity/"
        if not os.path.exists(self.path_output):
            os.makedirs(self.path_output)
            
    def load_data(self):
        """
        

        Returns
        -------
        None.

        """
        try:
            self.last_i = int(open(self.path_output+'/{}failsafe.txt'.format(self.focal_year), 'r').readline())
        except:
            self.last_i = 0
        if self.client_name:
            self.session = self.client.start_session()
            self.docs = self.collection.find({
                self.aut_list_variable:{'$ne':None},
                self.year_variable:self.focal_year
                },no_cursor_timeout  = True, session=self.session)
        else:
            self.docs = json.load(open("Data/docs/{}/{}.json".format(self.collection_name,self.focal_year)))
            
    def slip_cell(self,
                score_info,
                id_):
        var = [var for var in score_info if 'score_array' in var][0]
        var_id = [var_id for var_id in score_info[var] if 'id' in var_id][0]

        scores = []
        

        len_ = len(score_info[var]['score_array'])
        if len_ > 100000:
            nb_split = math.ceil(len_/100000)
            for i in range(nb_split):
                from_ = i*100000
                to_ = (i+1)*100000-1 if (i+1)*100000-1  < len_-1 else len_
                score = {var:{
                            var_id:score_info[var][var_id],
                            'score_array':score_info[var]['score_array'][from_:to_]},
                        'type':score_info['type']
                        }
                score.update({self.id_variable: id_})
                scores.append(score)
        else:
            score = {var:{
                    var_id:score_info[var][var_id],
                    'score_array':score_info[var]['score_array']},
                'type':score_info['type']
            }
            score.update({self.id_variable: id_})
            scores.append(score)
        return scores

    def insert_doc_output(self,
                      doc):
        """
        

        Parameters
        ----------
        doc : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if self.infos:
            if self.density:
                for ent in self.entity:
                    if ent in self.scores_infos:
                        for i in range(len(self.scores_infos[ent])):
                            id_ = doc[self.id_variable]
                            scores = self.slip_cell(self.scores_infos[ent][i],id_)
                            for score in scores:
                                self.list_of_insertion_sa.append(score)
                        
            
            for ent in self.infos:
                if self.client_name:
                    self.list_of_insertion_op.append(
                        #pymongo.UpdateOne(
                        {
                            self.id_variable: doc[self.id_variable], 
                            ent: self.infos[ent]
                            }
                                          #upsert = True)
                        )
                    self.client.admin.command('refreshSessions', [self.session.session_id], session=self.session)
                else:

                    self.list_of_insertion_op.append(
                        {
                            self.id_variable: doc[self.id_variable],
                            ent: self.infos[ent]
                            }
                        )
                  
                
    def save_outputs(self):
        """
        

        Returns
        -------
        None.

        """
        if self.client_name:
            if self.output_name not in self.db.list_collection_names():
                print("Init output_aut_comb collection with index on id_variable ...")
                self.collection_output = self.db[self.output_name]
                self.collection_output.create_index([ (self.id_variable,1) ])
            else:
                self.collection_output = self.db[self.output_name]
                    
            if self.list_of_insertion_op: 
                try:
                    self.db[self.output_name].insert_many(self.list_of_insertion_op)
                    last_i_file = open(self.path_output+'/{}failsafe.txt'.format(self.focal_year), 'w')
                    last_i_file.write(str(self.i))
                    last_i_file.close()
                except Exception as e:
                    file_object = open(self.path_output+'/{}.txt'.format(self.focal_year), 'a')
                    file_object.write(str(self.i))
                    file_object.close()

            if self.density:
                if self.list_of_insertion_sa:    
                    self.db[self.output_name].insert_many(self.list_of_insertion_sa)
        else:
            if self.list_of_insertion_op:
                with open(self.path_output + "/{}.json".format(self.focal_year), 'w') as outfile:
                    json.dump(self.list_of_insertion_op, outfile)              
            
            
                
    def init_doc_dict(self):
        """
        

        Returns
        -------
        None.

        """
        self.intra_authors_dist = {ent:[] for ent in self.entity}
        self.authors_infos = {ent:[] for ent in self.entity}
        self.authors_info_percentiles = {ent:[] for ent in self.entity}
        self.inter_authors_dist = {ent:[] for ent in self.entity}
        self.authors_infos_dist = {ent:[] for ent in self.entity}
        self.all_aut_ids =  {ent:[] for ent in self.entity}
        self.infos = dict()
        self.scores_infos = {}
        
        
    def structure_infos(self,
                      ent):
        authors_novelty = {
 
            'authors_novelty_{}_{}'.format(ent, str(self.windows_size)) :{
                'individuals_scores': self.authors_info_percentiles[ent],
                'iter_individuals_scores':self.authors_infos_dist[ent],
                'share_nb_aut_captured': self.nb_aut/self.true_nb_aut}
            }
        
        self.infos.update(authors_novelty)

        if self.density:

            dist_ = {'intra':self.intra_authors_dist,
                    'inter':self.inter_authors_dist}

            scores = []
            if self.client_name:
                for type_ in dist_:
                    infos = dist_[type_][ent]
                    for info in infos:
                        score = {'score_array_authors_novelty_{}_{}'.format(ent, str(self.windows_size)) : info}
                        score.update({'type': type_})
                        scores.append(score)
                self.scores_infos.update({ent:scores})
            else:
                scores.append(dist_)
                self.infos['authors_novelty_{}_{}'.format(ent, str(self.windows_size))].update({
                    self.year_variable:self.focal_year,
                    'score_array_authors_novelty_{}_{}'.format(ent, str(self.windows_size)) : {
                        'intra':self.intra_authors_dist[ent],
                        'inter':self.inter_authors_dist[ent]
                        }
                    })



            
    def get_author_papers(self,
                          auth_id):
        """
        

        Parameters
        ----------
        auth_id : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """

        if self.client_name:
            profile = self.collection_authors_years.find({
                self.aut_id_variable:auth_id,
                self.year_variable: {'$lt': self.focal_year,  '$gte': self.focal_year - self.windows_size} 
                }
                )
        else:
            profile = self.collection_authors_years[
                self.collection_authors_years[self.aut_id_variable] == auth_id
                ]

            profile = profile[
                profile[self.year_variable].between((self.focal_year-self.windows_size),(self.focal_year-1))
                ].to_dict("records")
        self.profile = profile
    
    
    def get_listed_papers(self):
        """
        

        Returns
        -------
        None.

        """
        txt_profile = {ent:[] for ent in self.entity}
        for year_profile in self.profile:
            if year_profile['embedded_abstract'] and 'abstract' in self.entity:
                txt_profile['abstract'] += year_profile['embedded_abstract'] 
            if year_profile['embedded_title'] and 'title' in self.entity :
                txt_profile['title']  += year_profile['embedded_title'] 
                
        self.profile = txt_profile

    def get_intra_infos(self,
                        items,
                        ent,
                        auth_id):
        """
        

        Parameters
        ----------
        items : TYPE
            DESCRIPTION.
        ent : TYPE
            DESCRIPTION.
        auth_id : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if items:
            n = len(items)
            # for arthor who have only one article before focal year
            if n > 0:
                self.authors_infos[ent].append(items) 
                self.all_aut_ids[ent].append(auth_id)
                
            if n >1:
                aut_dist = intra_cosine_similarity(items,
                                                   n,
                                                   self.distance_type)
                temp_dict = {str(self.aut_id_variable):auth_id}
                temp_dict.update(get_percentiles(aut_dist))

                score_dict = {'id': auth_id,
                              'score_array':aut_dist}
                self.authors_info_percentiles[ent] += [temp_dict]
                self.intra_authors_dist[ent] += [score_dict]
    
    def get_intra_dist(self,
                       doc):
        """


        Parameters
        ----------
        doc : dict
            Treated document.

        Returns
        -------
        None.

        """
        for auth in doc[self.aut_list_variable]: # TO CHANGE FOR OTHER DB
            auth_id = auth[self.aut_id_variable]
            self.get_author_papers(auth_id)
            self.get_listed_papers()
            for ent in self.profile:
                self.get_intra_infos(self.profile[ent],
                                     ent,
                                     auth_id)
            
                    
    def get_inter_dist(self,
                       ent):
        """
        

        Parameters
        ----------
        ent : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        # for all author
        for i in range(self.nb_aut):
            id_i = self.all_aut_ids[ent][i]
            # for all other authors
            for j in range(i+1,self.nb_aut):
                temp_list = []
                id_j = self.all_aut_ids[ent][j]
                # take each paper
                items = []
                for item in self.authors_infos[ent][i]:
                    # compare it with all papers of author j
                    items.append(item)
                    j_items = []
                    for j_item in self.authors_infos[ent][j]:
                        j_items.append(j_item)

                inter_paper_dist = similarity_dist(i = items, j = j_items, distance_type = self.distance_type)
                temp_list += inter_paper_dist

                temp_dict = {'ids' : [id_i,id_j]}

                self.inter_authors_dist[ent] += [{'ids' : [id_i,id_j], 'score_array':temp_list}]
                if temp_list:
                    temp_dict.update(get_percentiles(temp_list))
                # get percentiles
                self.authors_infos_dist[ent] += [temp_dict]
                    
                
    def compute_score(self,doc):
        """
        

        Parameters
        ----------
        doc : dict
            document from the embedded author collection.

        Returns
        -------
        None.

        """
        
        self.focal_paper_id = doc[self.id_variable]
        self.true_nb_aut =  len(doc[self.aut_list_variable])
        
        self.init_doc_dict()
        self.get_intra_dist(doc)
        if self.client_name:
            self.client.admin.command('refreshSessions', [self.session.session_id], session=self.session)

        for ent in self.entity:
            if self.client_name:
                self.client.admin.command('refreshSessions', [self.session.session_id], session=self.session)
            if len(self.intra_authors_dist[ent]) > 0:
                self.nb_aut = len(self.all_aut_ids[ent])
                
                if self.nb_aut > 1:
                    self.get_inter_dist(ent)
                    self.structure_infos(ent)


    def get_indicator(self,list_of_ids=None):
        """
        

        Returns
        -------
        None.

        """
        self.load_data()
        # Iterate over every docs 
        self.list_of_insertion_op = []
        self.list_of_insertion_sa = []
         
        self.i = 1 
        if list_of_ids:
            for id_ in tqdm.tqdm(list_of_ids):
                if self.i > self.last_i:
                    self.session = self.client.start_session()
                    doc = self.collection.find_one({self.id_variable:id_})
                    if doc:
                        self.focal_year = doc[self.year_variable]
                        if self.aut_list_variable in doc:
                            if doc[self.aut_list_variable]: 
                                self.compute_score(doc)
                                self.insert_doc_output(doc)
                            if self.i % 1000 == 0:
                                self.save_outputs()
                                self.list_of_insertion_op = []
                                self.list_of_insertion_sa = []
                self.i+=1
        else:
            for doc in tqdm.tqdm(self.docs):
                if self.i > self.last_i:
                    if doc[self.aut_list_variable]: 
                        self.compute_score(doc)
                        self.insert_doc_output(doc)
                    if self.i % 1000 == 0:
                        self.save_outputs()
                        self.list_of_insertion_op = []
                        self.list_of_insertion_sa = []

                self.i+=1
        self.save_outputs()


