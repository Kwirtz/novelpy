import pandas as pd 
from novelpy.utils.embedding import Embedding


embedding = Embedding(
		client_name = 'mongodb://localhost:27017',
		db_name = 'novelpy',
		year_variable = 'year',
		time_window = [2000,2002],
		id_variable = 'PMID',
		references_variable = 'refs_pmid_wos',
		auth_pubs_variable = 'pmid_list',
		id_auth_variable = 'AND_ID',
		pretrain_path = '/home/peltouz/Downloads/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0',
		title_variable = 'ArticleTitle',
		abstract_variable = 'a04_abstract',
		keywords_variable = 'Mesh_year_category',
		keywords_subvariable = 'DescUI',
		abstract_subvariable = 'AbstractText')

embedding.get_articles_centroid(
      collection_articles = 'articles',
      collection_embedding = 'articles_embedding')

print('centroid done')

embedding.feed_author_profile(
	collection_authors = 'authors',
        collection_embedding = 'articles_embedding',
        skip_ = 1,
        limit_ = 0)

print('authors profile created')

embedding.author_profile2papers(
	collection_authors = 'authors',
        collection_articles = 'articles',
        collection_articles_author_profile = 'articles_authors_profiles',
        skip_ = 1,
        limit_ = 0)

print('merged with articles database')

embedding.get_references_embbeding(
      collection_articles = 'articles',
      collection_embedding = 'articles_embedding',
      collection_ref_embedding = 'references_embedding',
      skip_ = 1,
      limit_ = 0)

print('references embedding created')





from novelpy.utils.embedding import Embedding


for focal_year in range(2000,2003):


	shibayama = novelpy.indicators.Shibayama2021(
		client_name = 'mongodb://localhost:27017',
		db_name = 'novelpy',
		collection_name = 'references_embedding',
		id_variable = 'PMID',
		year_variable = 'year',
		ref_variable = 'refs_embedding',
		entity = ['title_embedding','abstract_embedding'],
		focal_year = focal_year,
		embedding_dim = 200)

	shibayama.get_indicator()


	author_proximity = novelpy.indicators.Author_proximity(
	                 client_name = 'mongodb://localhost:27017',
	                 db_name =  'novelpy',
	                 collection_name = 'articles_authors_profiles',
	                 id_variable = 'PMID',
	                 year_variable = 'year',
	                 aut_profile_variable = 'authors_profiles',
	                 entity = ['title_profile','abs_profile'],
	                 focal_year = focal_year,
	                 windows_size = 5)

	author_proximity.get_indicator()