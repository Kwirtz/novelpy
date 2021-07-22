import itertools
import pandas as pd 

def Kscores(focal_paper_year, focal_paper_mesh_infos):
    meshs_df = pd.DataFrame(focal_paper_mesh_infos)
    
    # Novelty
    dim_new =  meshs_df[meshs_df['year']==focal_paper_year].shape[0]
    dim_mesh = meshs_df.shape[0]
    new_kw = dim_new/dim_mesh
    
    # Diversity
    groups = list(itertools.chain(*meshs_df.category.dropna()))
    unique_groups = set(groups)
    diversity_kw = len(unique_groups)/len(groups)
    
    scores = {
        'novelty_kw':new_kw,
        'diversity_kw':diversity_kw
        }
    return scores
