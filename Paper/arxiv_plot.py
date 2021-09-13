# https://www.kaggle.com/Cornell-University/arxiv/version/37

import pymongo
import tqdm
import re
client = pymongo.MongoClient('mongodb://localhost:27017')
mydb = client["arxiv"]
collection = mydb["test"]

docs = collection.find({},no_cursor_timeout=True)

validate = []
n = 0
for doc in tqdm.tqdm(docs):
        text = str(doc['title']).lower() + str(doc['abstract']).lower() 
        is_in_text = [re.search(w,text) for w in [i.lower() for i in ["bibliometric","indicator"]] if re.search(w,text) != None]
        if len(is_in_text) == 2:
            validate.append(doc['update_date'])
        else:
            continue
