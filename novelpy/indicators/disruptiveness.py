import pymongo
import numpy as np 

class Disruptiveness:

    def __init__(self,
                path2citnet):
        self.path2citnet = path2citnet


    def get_citation_cleaned_citation_network(self):
        citation_network = pd.read_json(self.path2citnet)
        citation_network = citation_network.dropna(subset=['refs_pmids'])
        citation_network = citation_network.drop('_id',axis = 1)
        citation_network = citation_network[citation_network['Journal_JournalIssue_PubDate_Year'] != '']
        citation_network = citation_network.explode('refs_pmids')
        self.citation_network = citation_network.set_index(['PMID', 'refs_pmids'])

    def compute_scores(focal_paper_id, focal_paper_year, focal_paper_refs):
        """
        Contrary to other
        indicators in this folder, Disruptiveness works at a document
         level because of the inefficiency of this

        Parameters
        ----------
        focal_paper_id : int
            Focal paper info from mongo
        
        focal_paper_year : int
            Year of publishing of the focal paper
            
        focal_paper_refs : list
            List of references present in the focal paper
            
        datacollection : pymongo.collection.Collection
            A collection to search for ref ID

        Returns
        -------
        Several Disruptiveness indicators.

        """

        citing_focal_paper_pmid = list(
            citation_network[self.citation_network.index.get_level_values('refs_pmids') == focal_paper_id
                             ].reset_index()['PMID'])

        citing_focal_paper = self.citation_network[
            self.citation_network.index.isin(citing_focal_paper_pmid, level='PMID')
            ].reset_index().groupby('PMID')['refs_pmids'].apply(list).reset_index()

        citing_ref_from_focal_paper = self.citation_network[
            citation_network.index.isin(focal_paper_refs, level='refs_pmids')
            ].reset_index()

        citing_ref_from_focal_paper = citing_ref_from_focal_paper[
            citing_ref_from_focal_paper['Journal_JournalIssue_PubDate_Year']>focal_paper_year
            ].reset_index().groupby('PMID')['refs_pmids'].apply(list).reset_index()

        citing_focal_paper = {
            row['PMID']:row['refs_pmids'] for index, row in citing_focal_paper.iterrows()
            }

        citing_ref_from_focal_paper = {
            row['PMID']:row['refs_pmids'] for index, row in citing_ref_from_focal_paper.iterrows()
            }


        J = set(citing_focal_paper.keys()).intersection(citing_ref_from_focal_paper.keys())
        I = np.setdiff1d(set(citing_focal_paper.keys()),J)
        K = np.setdiff1d(set(citing_ref_from_focal_paper.keys()),J)

        Jxc = [len(set(focal_paper_refs).intersection(cited_ref)) for cited_ref in citing_focal_paper.values()]
        
        J5 = [len_match_ref for len_match_ref in Jxc if len_match_ref > 4]
        
        Breadth = [pmid for pmid in citing_focal_paper
                   if not any([ref in citing_focal_paper.keys() for ref in citing_focal_paper[pmid]])]
        Depth = [pmid for pmid in citing_focal_paper
                   if any([ref in citing_focal_paper.keys() for ref in citing_focal_paper[pmid]])]

        try:
            return {focal_paper_id:
                    {'disruptiveness' :
                        {
                        'DI1': (len(I)-len(J))/(len(I)+len(J)+len(K)),
                        'DI5': (len(I)-len(J5))/(len(I)+len(J5)+len(K)),
                        'DI1nok': (len(I)-len(J))/(len(I)+len(J)),
                        'DI5nok': (len(I)-len(J5))/(len(I)+len(J5)),
                        'DeIn': sum(Jxc)/(len(I)+len(J)),
                        'Breadth' : len(Breadth)/(len(I)+len(J)),
                        'Depth' : len(Depth)/(len(I)+len(J))
                        }
                    }
                    }
        except: 
             return {focal_paper_id:
                    {'disruptiveness' :
                        {
                        'DI1': None,
                        'DI5': None,
                        'DI1nok': None,
                        'DI5nok': None,
                        'DeIn': None,
                        'Breadth' : None,
                        'Depth' : None
                        }
                    }
                    }
