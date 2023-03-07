import os
import tqdm
import json
import pymongo
import numpy as np
from collections import Counter


def get_q_journal_list(focal_year, variable, sub_variable, collection_name, year_variable,
                       keep_item_percentile = 50, client_name = None, db_name = None):
    if client_name:
        client = pymongo.MongoClient(client_name)
        db = client[db_name]
        collection = db[collection_name]    
        
    items = []
    for year in tqdm.tqdm(range(focal_year-3,focal_year)):
        if client_name:
            docs = collection.find({
                variable:{'$exists':'true'},
                year_variable:year
                })
        else:
            docs = json.load(open("Data/docs/{}/{}.json".format(collection_name,
                                                                     year)) )
        for doc in tqdm.tqdm(docs):
            if variable in doc:
                for ref in doc[variable]:
                    items.append(ref[sub_variable])

    count = Counter(items)                
    nb_cit = [count[item] for item in count]
    percentile = np.percentile(nb_cit, keep_item_percentile)
    list_of_items_restricted = [item for item in count if count[item] >= percentile]
    if not os.path.exists("Data/q_journal_list/"):
        os.makedirs("Data/q_journal_list/")
    with open("Data/q_journal_list/{}.json".format(focal_year), 'w') as outfile:
        json.dump(list_of_items_restricted, outfile)   
        

if __name__ == "__main__":
    for year in tqdm.tqdm(range(2017,2022)):
        get_q_journal_list(focal_year = year,
                           collection_name = "references",
                           year_variable = "publication_year",
                           client_name = "mongodb://localhost:27017",
                           db_name = "openAlex_novelty",
                           variable = "referenced_works",
                           sub_variable = "journal")