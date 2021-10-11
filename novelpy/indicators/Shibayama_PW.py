# inspired from https://github.com/DeyunYinWIPO/Novelty/blob/main/novelty_sci.py
import itertools
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class Novelty_embedding:
    
    def __init__(self,
                 var_id,
                 var_ref,
                 var_aut_profile,
                 var_year):
        """
        Description
        -----------
        Compute Shibayama et al (2021) novelty indicator and our alternative with author poximity

        Parameters
        ----------
        var_id : str
            identifier variable name.
        var_ref : str
            lembedded representation of references variable name.
        var_aut_profile : str
            embedded representation of author articles variable name.
        var_year : str
            year variable name.

        Returns
        -------
        None.

        """
        self.var_id = var_id
        self.var_ref = var_ref
        self.var_aut_profile = var_aut_profile
        self.var_year = var_year
        self.infos = dict()
        
        
    
    def cosine_similarity_dist(self,n,doc_mat):
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
    
    def get_percentiles(self,dist_list):
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
            nov_list.update({q: np.percentile(dist_list, q)})
            
        return nov_list
    
    def Shibayama2021(self,doc,entity):
        """
        

        Parameters
        ----------
        doc : dict
            document from the embedded reference collection.
        entity : str
            title or abstract.

        Returns
        -------
        None.

        """

        self.focal_paper_id = doc[self.var_id]
        n = len(doc[self.var_ref])
        doc_mat = np.zeros((n, 200))
        for i in range(n):
            item = doc[self.var_ref][i][entity]
            if item:
                doc_mat[i, :] =  item
        dist_list = self.cosine_similarity_dist(n,doc_mat)
        nov_list = self.get_percentiles(dist_list)
        
        references_novelty = {
            'Shibayama_{}'.format(entity) :nov_list
            }

        self.infos.update(references_novelty)

    def Author_proximity(self,doc,entity,windows_size):
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
        self.focal_paper_id = doc[self.var_id]
        nb_aut = len(doc[self.var_aut_profile])
        authors_mat = np.zeros((nb_aut, 200))
        intra_authors_dist = []
        authors_infos = []
        
        for i in range(nb_aut):
            items = doc[self.var_aut_profile][i][entity]
            if items:
                aut_item = [items[key] for key in items if int(key) > (doc[self.var_year]-windows_size) ]
                aut_item = list(itertools.chain.from_iterable(aut_item))
                aut_item = [item for item in aut_item if item]
                
                authors_infos.append(aut_item)
                
                n = len(aut_item)
                aut_mat = np.zeros((n, 200))
                for i in range(n):
                    aut_mat[i, :] = aut_item[i]
                            
                aut_dist = self.cosine_similarity_dist(n,aut_mat)
                intra_authors_dist += aut_dist
                
        intra_nov_list = self.get_percentiles(intra_authors_dist)
                    
        inter_authors_dist = []
        nb_cap = len(authors_infos)
        # for all author
        for i in range(nb_cap):
            # take each paper
            for item in authors_infos[i]:
                # for all other authors
                for j in range(i,nb_cap):
                    # compare it with all papers
                    for j_item in authors_infos[j]:
                        comb = np.array([item,j_item])
                        inter_paper_dist = cosine_similarity(comb)[0,1]
                        inter_authors_dist.append(inter_paper_dist)
                
        inter_nov_list = self.get_percentiles(inter_authors_dist)
            
        authors_novelty = {
            'authors_novelty_{}_{}'.format(entity, str(windows_size)) :{
                'intra':intra_nov_list,
                'inter':inter_nov_list}
            }
        self.infos.update(authors_novelty)


    def update_paper_values(self,tomongo = True):

        if tomongo:
            try:
                query = { self.var_id: self.focal_paper_id}
                newvalue =  { '$set': self.infos}
                db['output'].update_one(query,newvalue)
            except Exception as e:
                print(e)
        else:
            return {self.focal_paper_id:self.infos}

