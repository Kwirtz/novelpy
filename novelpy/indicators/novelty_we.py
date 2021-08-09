import tqdm
import yaml 
# From https://github.com/DeyunYinWIPO/Novelty/blob/main/novelty_sci.py

import spacy
import scispacy
import numpy as np
import csv
from sklearn.metrics.pairwise import cosine_similarity
from joblib import Parallel, delayed

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

def novel(txt):
    n = len(txt)
    w = np.zeros((n, d))

    q_list = [100, 99, 95, 90, 80, 50]
    # Assign word embedding
    for i in range(n):
        tokens = nlp(txt[i])
        w[i, :] = np.sum([t.vector for t in tokens], axis=0) / len(tokens)
 
    # Compute similarity
    cos_sim = cosine_similarity(w)
    dist_list = []
    for i in range(n):
        for j in range(i+1,n):
            dist_list.append(1 - cos_sim[i][j])

    # Take p-percentile value to compute novelty
    nov_list = []
    for q in q_list:
        nov_list.append([q, np.percentile(dist_list, q)])

    return nov_list, dist_list



def compute_score(pmid): 
    data = Dataset(var = 'refs_pmid_wos',
                   var_id = 'PMID',
                   focal_year = 2000,
                   var_year = 'Journal_JournalIssue_PubDate_Year',
                   client_name = pars['client_name'], 
                   db_name =  pars['db_name'],
                   collection_name = pars[db]['collection_name'])
    doc = data.collection.find({data.VAR_PMID:pmid})[0]
    titles = []
    abstracts = []
    for pmid_ref in doc[data.VAR]:
       doc_ref =  data.collection.find({data.VAR_PMID:pmid_ref})[0]
       try:
           titles.append(doc_ref['ArticleTitle'])
       except:
           pass
       try:
           abstracts.append(doc_ref['a04_abstract'][0]['AbstractText'])
       except:
           pass
    try:
        novelty_title = novel(titles)
    except:
        novelty_title = None
    try:
        novelty_abstract = novel(abstracts)
    except:
        novelty_abstract = None
    print(novelty_abstract)
    print(novelty_title)
    query = { data.VAR_PMID: pmid }
    newvalues = { '$set': {'novelty_title':novelty_title,
                           'novelty_abstarct':novelty_abstract}}
    data.collection.update_one(query,newvalues)
    

from novelpy import Dataset
with open(r"C:\Users\Beta\Documents\GitHub\Taxonomy-of-novelty\mongo_config.yaml", "r") as infile:
    pars = yaml.safe_load(infile)['PC_BETA']
db= 'pkg'


nlp = spacy.load(
    "D:/PKG/txt_modles/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0")
d = 200
# Set q for novel_q percentile ranks
q_list = [100, 99, 95, 90, 80, 50]

#id_range = range(1,32000000)

id_range = range(14563551,14563581)
# Parallel(n_jobs=10)(
#     delayed(compute_score)(pmid) for pmid in tqdm.tqdm(id_range))


from multiprocessing import Process, Manager
processes = []
for pmid in tqdm.tqdm(list(id_range),desc='start'):
    
    p = Process(target=compute_score, args=(pmid,))
    p.start()
    processes.append(p)

for p in tqdm.tqdm(processes,desc = 'join'):
    p.join()
            

# for pmid in tqdm.tqdm(id_range):
#     compute_score(pmid)

   
          