import requests
from tqdm import tqdm
import shutil
import io
import os
import pymongo
import json

def download_sample(client_name = None):
    
    
    url = 'https://github.com/Kwirtz/data_sample/blob/main/novelpy/docs.zip?raw=true'
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get('content-length', 0))
    with open("docs.zip", 'wb') as file, tqdm(
        desc="docs.zip",
        total=total,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=1024):
            size = file.write(data)
            bar.update(size)
    shutil.unpack_archive("docs.zip","Data/docs")
    """
    with open("sample_data.zip", 'rb') as f:
        buf = f.read()
        z = zipfile.ZipFile(io.BytesIO(buf))
        z.extractall()
   """
    os.remove("docs.zip")
    
    
    
    if client_name:
        print("Loading to mongo...")
        Client = pymongo.MongoClient(client_name)
        db = Client["novelty_sample_test"]
        collection_meshterms = db["meshterms"]
        collection_references = db["references"]
        collection_authors = db["authors"]
        for file in os.listdir("Data/docs/references_sample"):
            with open("Data/docs/references_sample" + "/{}".format(file), 'r') as infile:
                docs = json.load(infile)
            collection_references.insert_many(docs)
        for file in os.listdir("Data/docs/meshterms_sample"):
            with open("Data/docs/meshterms_sample" + "/{}".format(file), 'r') as infile:
                docs = json.load(infile)
            collection_meshterms.insert_many(docs)
        with open("Data/docs/authors_sample.json", 'r') as infile:
            docs = json.load(infile)        
        collection_authors.insert_many(docs)
        
