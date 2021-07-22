import os
import pylab as plt
import pandas as pd
#from text_algorithm.sbmtm import sbmtm
import gensim
from top2vec import Top2Vec
#import graph_tool.all as gt
import itertools
import time
import yaml

with open("..\mongo_config.yaml", "r") as infile:
    pars = yaml.safe_load(infile)['PC_BETA']


var = pars['text']['var']
year_var = pars['text']['year_var']
data = Dataset(client_name = pars['client_name'], 
               db_name = pars['text']['db_name'],
               collection_name = pars['text']['collection_name'],
               var = var)




client = pymongo.MongoClient( pars['client_name'])
db = client[pars['db_name']]
collection = db[pars['pkg']['collection_name']]
docs = collection.find({yv:{'$exists':1}})
yv = pars['pkg']['year_var']
for doc in tqdm.tqdm(docs):
    try:
        doc_infos = {yv: int(doc[yv])}
        query = {'PMID':int(doc['PMID'])}
        newvalues = {'$set':doc_infos}
        collection.update_one(query,newvalues)
    except:
        pass

docs = collection.find({yv:{'$exists':1}})

#Run TOP2VEC MODEL BY YEAR

for year in range(1987,2021):
    
    docs = data.collection.find({
        '$and': [
            {var:{'$exists':'true'}},
            {year_var:{'$eq':str(year)}}
            ]
        }
        )

    # Clean abs
    docs_lst = [doc[var][0]['AbstractText'] for doc in tqdm.tqdm(docs)]
    model = Top2Vec(documents=docs_lst, speed="deep-learn", workers=50)
    model.save('models/TOP2VEC_PKG_'+str(year))
    
    
#docs_tokenised = {doc['PM']:clean_and_tokenize(doc[var][0]['AbstractText'],remove_stops = False)
#                  for doc in tqdm.tqdm(docs)}
##docs_ngram = make_ngram(list(docs_tokenised.values()),3,100)
#docs_nested = list(map(lambda x : ' '.join(x),docs_tokenised.values()))
#time.time() - t




## TOP2VEC

topic_words, word_scores, topic_nums = model.get_topics(model.get_num_topics())
docs_vec = model._get_document_vectors()
tops_vec = model.topic_vectors
model.save('models/test2')
#topics = _find_topic_words_and_scores(model,100)

docs_topic_dist = []
for doc in tqdm.tqdm(model.documents, total= model.documents.shape[0]):
    docs_topic_dist.append(get_topic_dist(model,doc,0.1,1))

data = pd.DataFrame(docs_topic_dist)
ind = Diversity(data,'all')
ind.weitzman(pars['div_params']['weitzman'][0])


ind.metric
docs_cos = np.inner(docs_vec, tops_vec)
docs_cos.shape

## TOPSBM

model = sbmtm()
model.make_graph(list(docs_tokenised.values()),documents=list(docs_tokenised.keys()))
gt.seed_rng(32) ## seed for graph-tool's random number generator --> same results
model.fit()
time.time() - t
model.topics()
## select a document (by its index)
i_doc = 3
print(model.documents[i_doc])
## get a list of tuples (topic-index, probability)
model.topicdist(i_doc,l=0)
model.topics(l=1)
model.get_groups(l=0)["p_tw_d"].shape
model.plot_topic_dist(lvl)

lvl = 0
word_mix = model.topics(l=lvl)
# Create tidier names
topic_name_lookup = {
    key: "_".join([x[0] for x in values[:5]]) for key, values in word_mix.items()
}
topic_names = list(topic_name_lookup.values())

# Extract the topic mix df
topic_mix_ = pd.DataFrame(
    model.get_groups(l=lvl)["p_tw_d"].T,
    columns=topic_names,
    index=model.documents,
    )

topic_mix_.columns
