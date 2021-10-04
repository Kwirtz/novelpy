# inspired from https://github.com/DeyunYinWIPO/Novelty/blob/main/novelty_sci.py
import itertools
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class Novelty_embedding:
    
    def __init__(self,
                 var_ref,
                 var_aut_profile):
        
        self.var_ref = var_ref
        self.var_aut_profile = var_aut_profile
        
    
    def cosine_similarity_dist(n,doc_mat):
        """
        

        Parameters
        ----------
        list_ : TYPE
            DESCRIPTION.

        Returns
        -------
        dist_list : TYPE
            DESCRIPTION.

        """

        # Compute similarity
        cos_sim = cosine_similarity(doc_mat)
        dist_list = []
        for i in range(n):
            for j in range(i+1,n):
                dist_list.append(1 - cos_sim[i][j])
    
        return dist_list
    
    def get_percentiles(dist_list):
        
        nov_list = dict()
        for q in [100, 99, 95, 90, 80, 50, 20, 10, 5, 1, 0]:
            nov_list.update({q: np.percentile(dist_list, q)})
            
        return nov_list
    
    def Shibayama2021(doc,entity):
        """
        

        Parameters
        ----------
        doc : TYPE
            DESCRIPTION.
        entity : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        n = len(doc[self.var_ref])
        doc_mat = np.zeros((n, 200))
        for i in range(n):
            doc_mat[i, :] = doc[self.var_ref][i][entity]
        dist_list = cosine_similarity_dist(n,doc_mat)
        nov_list = get_percentiles(dist_list)
        
        return nov_list

    def Author_proximity(doc,entity,window_size):
        """
        

        Parameters
        ----------
        doc : TYPE
            DESCRIPTION.
        entity : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        
        nb_aut = len(doc[self.var_aut_profile])
        authors_mat = np.zeros((nb_aut, 200))
        intra_authors_dist = []
        authors_infos = []
        
        for i in range(nb_aut):
            items = doc[self.var_aut_profile][i][entity]
            if items:
                aut_item = [items[key] for key in items if int(key) > (doc[self.var_year]-windows_size) ]
                aut_item = list(itertools.chain.from_iterable(aut_item))
                authors_infos.append(aut_item)
                
                n = len(aut_item)
                aut_mat = np.zeros((n, 200))
                for i in range(n):
                    aut_mat[i, :] = aut_item[i]
                aut_dist = cosine_similarity_dist(n,aut_mat)
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
            
        return {
            'authors_novelty':{
                'intra':intra_nov_list,
                'inter':inter_nov_list}
            }


