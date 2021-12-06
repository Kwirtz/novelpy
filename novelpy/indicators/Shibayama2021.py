# inspired from https://github.com/DeyunYinWIPO/Novelty/blob/main/novelty_sci.py
import itertools
import numpy as np
from novelpy.utils.run_indicator_tools import Dataset
import pymongo


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
    
    
    
    def compute_score(self):
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
            dist_list = self.cosine_similarity_dist(n,doc_mat)
            nov_list = self.get_percentiles(dist_list)
            
            references_novelty = {
                'Shibayama_{}'.format(ent) :nov_list
                }

            self.infos.update(references_novelty)

    def get_indicator(self):
       
        if self.client_name:
            self.docs = self.collection.find({
                self.variable:{'$exists':'true'},
                self.year_variable:self.focal_year
                })
        else:
            self.docs = json.load(open("Data/docs/{}/{}.json".format(self.collection_name,self.focal_year)))

        # Iterate over every docs 
        list_of_insertion = []
        for doc in tqdm.tqdm(docs):
            self.infos = dict()
            self.compute_score(doc, self.entity)
            if self.client_name:
                list_of_insertion.append(pymongo.UpdateOne({self.id_variable: doc[self.id_variable]},
                                                           {'$set': {self.key: self.infos}},
                                                           upsert = True))
            else:
                list_of_insertion.append({self.id_variable: doc[self.id_variable],self.key: self.infos})

        if self.client_name:
            self.db['output'].bulk_write(list_of_insertion)
        else:
            with open(self.path_output + "/{}.json".format(self.focal_year), 'w') as outfile:
                json.dump(list_of_insertion, outfile)        
    


