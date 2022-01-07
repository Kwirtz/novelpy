import pandas as pd 
docs = pd.read_json("{}/authors_profiles.json".format('Data'))
print(docs)
print(docs[docs['AND_ID' == 2]].to_dict())