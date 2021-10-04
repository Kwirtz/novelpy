import pymongo

authors = [
    
    {"PMID":1,
     "year":2001,
     "Authors":[
         {"AUID":1,"papers_done":[{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]},{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]}]},
         {"AUID":2,"papers_done":[{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]},{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]}]}
    ]},
    
    {"PMID":2,
     "year":2003,
     "Authors":[
         {"AUID":1,"papers_done":[{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]},{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]}]},
         {"AUID":2,"papers_done":[{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]},{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]}]}
     ]
    }
    ]


references = [
    
    {"PMID":1,
     "year":2001,
     "c04_referencelist":[{"item":"0006-3002", "year":1971},{"item":"0026-895X", "year":1968}]
     },
    
    {"PMID":2,
     "year":2003,
     "c04_referencelist":[{"item":"0002-7863", "year":1975},{"item":"0002-7863", "year":1973}]
     }
    
    ]

# year = creation of meshterms, needed for ?????
keywords = [
    
    {"PMID":1,
     "year":2001,
     "a06_meshheadinglist":[{"item":"D005583", "year":1971},{"item":"D009682", "year":1968}]
     },
    
    {"PMID":2,
     "year":2003,
     "a06_meshheadinglist":[{"item":"D000445", "year":1975},{"item":"D000818", "year":1973}]
     }
    
    ]



db_output = [
    {"PMID":1,
     "c04_ref":{"Atypicality":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Comonness":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Foster":0.34, "Disruptiveness": 0.8},
     "a06_mesh":{"Atypicality":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Comonness":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Foster":0.34},
     "authors_embedding":{"Atypicality":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Comonness":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Foster":0.34},
    },
    {"PMID":2,
     "c04_ref":{"Atypicality":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Comonness":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Foster":0.34, "Disruptiveness": 0.8},
     "a06_mesh":{"Atypicality":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Comonness":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Foster":0.34},
     "authors_embedding":{"Atypicality":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Comonness":{"10per":0.20,"Median":0.4,"Density":[0.2,0.3,0.4]},"Foster":0.34},     
     }
    ]

client = pymongo.MongoClient('mongodb://localhost:27017')
mydb = client["pkg"]

collection_authors = mydb["example_authors"]
collection_references =  mydb["example_references"]
collection_keywords =  mydb["example_keywords"]
collection_output =  mydb["example_output"]

collection_authors.insert_many(authors)
collection_references.insert_many(references)
collection_keywords.insert_many(keywords)
collection_output.insert_many(db_output)