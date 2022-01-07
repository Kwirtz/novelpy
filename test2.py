
from novelpy.utils.embedding import Embedding

embedding = Embedding(
		data_path = 'Data',
		#client_name = 'mongodb://localhost:27017',
		#db_name = 'novelpy',
		year_variable = 'year',
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


embedding.feed_author_profile(
	collection_authors = 'authors',
        collection_embedding = 'articles_embedding',
        skip_ = 1,
        limit_ = 0)

embedding.author_profile2papers(
	collection_authors = 'authors',
        collection_articles = 'articles',
        collection_articles_author_profile = 'articles_author_profile',
        skip_ = 1,
        limit_ = 0)

embedding.get_references_embbeding(
      collection_articles = 'articles',
      collection_embedding = 'articles_embedding',
      collection_ref_embedding = 'references_embedding',
      skip_ = 1,
      limit_ = 0)
