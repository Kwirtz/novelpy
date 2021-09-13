import pymongo


db_input = [
    {"PMID":1,
     "year": 2001,
     "CR_year_category":[{"ref_name":"lancet","year":1990, "doi":"10/123"},{"ref_name":"plosone","year":1995} ],
     "Mesh_year_category":[{"desc_ui":"M1234", "year":1990,"cat":"Virusidontknow"},{"desc_ui":"M12345", "year":1991,"cat":"vaccineidontknow"}],
     "Ref_we":[{"ref_name":"lancet","year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3]},{"ref_name":"plosone","year":1995,"abstract_we":[0.3,4,0.2,1.3],"title_we":[21,10,0.2,0.3]} ],
     "Authors":[
         {"AUID":1,"papers_done":[{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]},{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]}]},
         {"AUID":2,"papers_done":[{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]},{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]}]}
             ]
     },
    {"PMID":2,
     "year": 2002,
     "CR_year_category":[{"ref_name":"lancet","year":1993},{"ref_name":"plosone","year":1991} ],
     "Mesh_year_category":[{"desc_ui":"X1234", "year":1995,"cat":"Virusidontknow"},{"desc_ui":"M123456", "year":1991,"cat":"vaccineidontknow"}],
     "Ref_we":[{"ref_name":"lancet","year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3]},{"ref_name":"plosone","year":1995,"abstract_we":[0.3,4,0.2,1.3],"title_we":[21,10,0.2,0.3]} ],
     "Authors":[
         {"AUID":1,"papers_done":[{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]},{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]}]},
         {"AUID":2,"papers_done":[{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]},{"year":1990,"abstract_we":[0,1,2,3],"title_we":[0.89,100,2,3], "keywords":["math","cs"]}]}
     ]
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
collection_input = mydb["example_input"]
collection_output =  mydb["example_output"]

collection_input.insert_many(db_input)
collection_output.insert_many(db_output)