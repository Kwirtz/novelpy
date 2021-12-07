# inspired from https://github.com/DeyunYinWIPO/Novelty/blob/main/novelty_sci.py
import itertools
import numpy as np
from novelpy.utils.run_indicator_tools import Dataset
import pymongo
import tqdm
from sklearn.metrics.pairwise import cosine_similarity

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

class Shibayama2021(Dataset):
    
    def __init__(self,
                 client_name = None, 
                 db_name =  None,
                 collection_name = None,
                 id_variable = None,
                 year_variable = None,
                 ref_variable = None,
                 entity = None,
                 focal_year = None):
        """
        Description
        -----------
        Compute Shibayama et al (2021) novelty indicator and our alternative with author poximity

        Parameters
        ----------
        id_variable : str
            identifier variable name.
        ref_variable : str
            lembedded representation of references variable name.
        aut_profile_variable : str
            embedded representation of author articles variable name.
        year_variable : str
            year variable name.

        Returns
        -------
        None.

        """
        self.id_variable = id_variable
        self.ref_variable = ref_variable
        self.year_variable = year_variable
        self.entity = entity

        Dataset.__init__(
            self,
            client_name = client_name,
            db_name = db_name,
            collection_name = collection_name ,
            id_variable = id_variable,
            year_variable = year_variable,
            focal_year = focal_year)
    
    
    
    def compute_score(self,doc,entity):
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
        for ent in entity:
            self.focal_paper_id = doc[self.id_variable]
            n = len(doc[self.ref_variable])
            doc_mat = np.zeros((n, 200))
            for i in range(n):
                item = doc[self.ref_variable][i][ent]
                if item:
                    doc_mat[i, :] =  item
            dist_list = cosine_similarity_dist(n,doc_mat)
            nov_list = get_percentiles(dist_list)
            
            references_novelty = {
                'Shibayama_{}'.format(ent) :nov_list
                }

            self.infos.update(references_novelty)

    def get_indicator(self):
       
        if self.client_name:
            self.docs = self.collection.find({
                self.ref_variable:{'$ne':None},
                self.year_variable:self.focal_year
                })
        else:
            self.docs = json.load(open("Data/docs/{}/{}.json".format(self.collection_name,self.focal_year)))

        # Iterate over every docs 
        list_of_insertion = []
        for doc in tqdm.tqdm(self.docs):
            self.infos = dict()
            if len(doc[self.ref_variable])>1: 
                self.compute_score(doc, self.entity)

                if self.client_name:
                    list_of_insertion.append(pymongo.UpdateOne({self.id_variable: doc[self.id_variable]},
                                                               {'$set': {'Shibayama': self.infos}},
                                                               upsert = True))
                else:
                    list_of_insertion.append({self.id_variable: doc[self.id_variable],'Shibayama': self.infos})
        
        if self.client_name:
            if "output" not in self.db.list_collection_names():
                print("Init output collection with index on id_variable ...")
                self.collection_output = self.db["output"]
                self.collection_output.create_index([ (self.id_variable,1) ])
            else:
                self.collection_output = self.db["output"]
                
            self.db['output'].bulk_write(list_of_insertion)
        else:
            with open(self.path_output + "/{}.json".format(self.focal_year), 'w') as outfile:
                json.dump(list_of_insertion, outfile)        
    


