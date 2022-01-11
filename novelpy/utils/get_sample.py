import requests
from tqdm import tqdm
import shutil
import io
import os
import pymongo
import json

def download_sample(client_name = None):
    
    collection_list =["Citation_net","Meshterms", "Ref_Journals", "Title_abs", "authors"]
    for col in collection_list:
        col = col+ "_sample"
        url = 'https://zenodo.org/record/5768348/files/{}.zip?download=1'.format(col)
        resp = requests.get(url, stream=True)
        total = int(resp.headers.get('content-length', 0))
        with open("{}.zip".format(col), 'wb') as file, tqdm(
            desc="{}.zip".format(col),
            total=total,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in resp.iter_content(chunk_size=1024):
                size = file.write(data)
                bar.update(size)
        shutil.unpack_archive("{}.zip".format(col),"Data/docs")
        """
        with open("sample_data.zip", 'rb') as f:
            buf = f.read()
            z = zipfile.ZipFile(io.BytesIO(buf))
            z.extractall()
        """
        os.remove("{}.zip".format(col))
        
        
        
        if client_name:
            print("Loading to mongo...")
            Client = pymongo.MongoClient(client_name)
            db = Client["novelty_sample"]
            collection = db[col]
            collection.create_index([ ("PMID",1) ])
            collection.create_index([ ("year",1) ])
            for file in os.listdir("Data/docs/{}".format(col)):
                with open("Data/docs/{}".format(col) + "/{}".format(file), 'r') as infile:
                    docs = json.load(infile)
                collection.insert_many(docs)