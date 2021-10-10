import yaml
from novelpy.cleaner import Embedding
import pandas as pd
import argparse
import yaml
parser = argparse.ArgumentParser(
    description='50 chunks')

parser.add_argument('-from_')
args = parser.parse_args()
from_ = int(args.from_)

with open(r"C:\Users\Beta\Documents\GitHub\Taxonomy-of-novelty\mongo_config.yaml", "r") as infile:
    pars = yaml.safe_load(infile)['PC_BETA']
db= 'pkg'
client_name = pars['client_name']
db_name = 'PKG'
collection_articles = 'articles'
collection_authors = 'authors'
var_year = 'Journal_JournalIssue_PubDate_Year'
var_id = 'PMID'
var_id_list = 'pmid_list'
var_pmid_list = 'refs_pmid_wos'
var_auth_id = 'AND_ID'
var_abstract = 'a04_abstract'
var_title = 'ArticleTitle'
var_keyword = 'a06_meshheadinglist'
pretrain_path = "C:/Users/Beta/Documents/GitHub/Taxonomy-of-novelty/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0"
author_ids_list = pd.read_json('D:/PKG/final_folder_260721/Data/authors_id.json')
author_ids_list = author_ids_list[var_auth_id].to_list()


embedding = Embedding(
    client_name,
    db_name,
    collection_articles,
    collection_authors,
    var_year,
    var_id,
    var_pmid_list,
    var_id_list,
    var_auth_id,
    pretrain_path,
    var_title,
    var_abstract,
    var_keyword)

# embedding.get_articles_centroid(pmid_start = 1,
#                          pmid_end = 33*10**6,
#                          chunk_size=1000)

# chunk = round((18.6*10**6)/50)
# from_ = list(range(1,round(18.6*10**6),chunk))[from_]


# embedding.feed_author_profile(author_ids_list[from_:from_+chunk])

# embedding.author_profile2papers()

# embedding.get_references_embbeding(skip_ = 1, limit_ = 11*10**6)
embedding.get_references_embbeding(skip_ = 11*10**6, limit_ = 11*10**6)
# embedding.get_references_embbeding(skip_ = 22*10**6, limit_ = 11*10**6)