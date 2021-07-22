import pymongo
import numpy as np 

def Disruptiveness(focal_paper_id, focal_paper_year, focal_paper_refs, df):
    """
    Contrary to other
    indicators in this folder, Disruptiveness works at a document level.

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

    # citing_focal_paper = {
    #     doc['PMID']:doc['refs_pmids'] for doc in datacollection.find(
    #         {
    #             'refs_pmids': focal_paper_id
    #         })
    # }

    # citing_ref_from_focal_paper = {
    #     doc['PMID']:doc['refs_pmids'] for doc in datacollection.find(
    #         {
    #             'Journal_JournalIssue_PubDate_Year':{'$gt':focal_paper_year},
    #             'refs_pmids':{'$in':focal_paper_refs}
    #         })
    # }
        
        
    citing_focal_paper = df[df['refs_pmids'].apply(lambda x: focal_paper_id  in x)]
    citing_ref_from_focal_paper = df[df['refs_pmids'].apply(lambda x: any([ref in x for ref in focal_paper_refs]))]
    citing_ref_from_focal_paper = citing_ref_from_focal_paper[citing_ref_from_focal_paper.year > focal_paper_year]
    
    
    citing_focal_paper = {row['pmid']:row['refs_pmids'] for index, row in citing_focal_paper.iterrows()}
    citing_ref_from_focal_paper = {row['pmid']:row['refs_pmids'] for index, row in citing_ref_from_focal_paper.iterrows()}


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
        return {
            'disruptiveness' :{
                'DI1': (len(I)-len(J))/(len(I)+len(J)+len(K)),
                'DI5': (len(I)-len(J5))/(len(I)+len(J5)+len(K)),
                'DI1nok': (len(I)-len(J))/(len(I)+len(J)),
                'DI5nok': (len(I)-len(J5))/(len(I)+len(J5)),
                'DeIn': sum(Jxc)/(len(I)+len(J)),
                'Breadth' : len(Breadth)/(len(I)+len(J)),
                'Depth' : len(Depth)/(len(I)+len(J))
                }
            }
    except: 
         return {
            'disruptiveness' :{
                'DI1': None,
                'DI5': None,
                'DI1nok': None,
                'DI5nok': None,
                'DeIn': None,
                'Breadth' : None,
                'Depth' : None
                }
            }