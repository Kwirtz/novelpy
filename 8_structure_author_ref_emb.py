import argparse
import yaml
parser = argparse.ArgumentParser(
    description='50 chunks')

parser.add_argument('-skip_')
args = parser.parse_args()
skip_ = int(args.skip_)

with open(r"C:\Users\pierre\Documents\GitHub\Taxonomy-of-novelty\mongo_config.yaml", "r") as infile:
    pars = yaml.safe_load(infile)['PC_BETA']

from novelpy.utils.embedding import Embedding

embedding = Embedding(
      year_variable = 'year',
      time_range = range(2000,2016),
      id_variable = 'PMID',
      client_name = 'mongodb://Pierre:ilovebeta67@localhost:27017/',
      db_name = 'novelty_final',
      references_variable = 'refs_pmid_wos',
      pretrain_path = r'D:\pretrain\en_core_sci_lg-0.4.0\en_core_sci_lg\en_core_sci_lg-0.4.0',
      title_variable = 'ArticleTitle',
      abstract_variable = 'a04_abstract',
      abstract_subvariable = 'AbstractText',
      id_auth_variable = 'AID',
      auth_pubs_variable = 'PMID_list')



#embedding.get_articles_centroid(
#      collection_articles = 'Title_abs_sample',
#      collection_embedding = 'embedding')


embedding.feed_author_profile(
    collection_authors = 'a02_authorlist_AID',
        collection_embedding = 'articles_embedding',
        skip_ = skip_,
        limit_ = 1000000)

print('authors profile created')

# embedding.author_profile2papers(
#     collection_authors = 'a02_authorlist_AID',
#         collection_articles = 'authors_sample',
#         collection_articles_author_profile = 'authors_sample',
#         skip_ = 1,
#         limit_ = 0)

# print('merged with articles database')

# embedding.get_references_embbeding(
#       collection_articles = 'articles',
#       collection_embedding = 'articles_embedding',
#       collection_ref_embedding = 'references_embedding',
#       skip_ = 1,
#       limit_ = 0)

# print('references embedding created')

# from novelpy.indicators.Author_proximity import Author_proximity

# for year in range(2000,2011):
#     author = Author_proximity(client_name = 'mongodb://Pierre:ilovebeta67@localhost:27017/',
#                      db_name = 'novelty_sample',
#                      collection_name = 'authors_sample',
#                      id_variable = 'PMID',
#                      year_variable = 'year',
#                      aut_profile_variable = 'authors_profiles',
#                      aut_id_variable = 'AID',
#                      entity = ['title_profile','abs_profile'],
#                      focal_year = year,
#                      windows_size = 5)
    
#     author.get_indicator()
