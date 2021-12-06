.. _Utils:

Utils
=====

.. _cooc_utils:

cooc_utils
------------

Most of the indicators consider that new ideas are created by combining already existing ones. In that end they look at the combination of items (Journals cited, keywords used, ...). cooc_utils creates an adjacency matrix that retraces the historic of these combination done in a given year.


.. py:function:: create_cooc(var, sub_var, year_var, collection_name, client_name = None, db_name = None, time_window = range(1980,2021), weighted_network = False, self_loop = False)

   Create co-occurence matrix 

   :param str var: The key of interest in the dict
   :param str sub_var: The key where the name of the variable is
   :param str year_var: The key that gives the year of the paper
   :param str collection_name: Name of the collection (either Mongo or Json) where the data is
   :param str client_name: name of the mongdb client
   :param str db_name: name of the mongdb Database
   :param range time_window: Compute the cooc for the years in range
   :param str weighted_network: False if you want a combinaisons that appears multiple time in a single paper to be accounted as 1
   :param str self_loop: True if you want the diagonal in the cooc-matrix

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 

.. _embedding:

embedding
------------

In order to use the indicators of Shibayama et al (2021) and the one on authors, it is necessary to embed the entities first. This function only works via mongo for the moment as it is impractical on large data sets. As these indicators are easily usable with small datasets, a version without mongo will be quickly developed.


.. py:function:: Embedding(client_name, db_name, collection_articles, collection_authors, collection_keywords, collection_embedding,  var_year, var_id, var_pmid_list, var_id_list, var_auth_id, pretrain_path, var_title, var_abstract, var_keyword, subvar_keyword)

    - Compute semantic centroid for each paper (abstract and title)
    - Create embedded references profile for each article.
    - Compute an author profile of embedded articles per year and store it for each article.

   :param str client_name: mongo client name
   :param str db_name: mongo db name
   :param str collection_articles: mongo collection name for articles
   :param str collection_authors: mongo collection name for authors
   :param str collection_keyword: mongo collection for articles keywords
   :param str collection_embedding: mongo collection for articles embedding
   :param str var_year: year variable name
   :param str var_id: identifier variable name
   :param str var_auth_id: authors identifer variable name
   :param str pretrain_path: path to the pretrain word2vec: 'your/path/to/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0
   :param str var_title: title variable name
   :param str var_abstract: abstract variable name
   :param str var_keyword: keyword variable name
   :param str subvar_keyword: keyword subvariable name

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 



.. code-block:: python

   embedding = Embedding(
       client_name = 'mongodb://localhost:27017',
       db_name = 'novelty',
       collection_articles = 'references_embedding',
       collection_authors = 'authors_embedding',
       collection_keywords = 'meshterms',
       collection_embedding = 'articles_embedding',
       var_year = 'year',
       var_id = 'PMID',
       var_id_list = 'pmid_list',
       var_pmid_list = 'refs_pmid_wos',
       var_auth_id = 'AND_ID',
       pretrain_path = 'path/to/pre/train',
       var_title = 'ArticleTitle',
       var_abstract = 'a04_abstract',
       var_keyword = 'Mesh_year_category',
       subvar_keyword = 'DescUI')

In order to build the profile of references and authors, it is first necessary to give a semantic representation to each article. The first function to use is ``get_articles_centroid``.


.. code-block:: python

   embedding.get_articles_centroid(pmid_start = pmid_start,
                          pmid_end = pmid_end,
                          chunk_size=1000)

To compute Shibayama et al. 2021 indicators, it is necessary to construct a profile of references for each item. One can also select the time window to consider.


.. code-block:: python

   embedding.get_references_embbeding(
      from_year = 2000,
      to_year = 2010,
      skip_ = skip_,
      limit_ = limit_)

The author proximity works in a two step process, first it creates an profile for each authors in a separate database for all year were a given author has a publication. Then two construct the indicateur at the paper level, all authors profile a then import from the authors database. It select only authors representation before the given document publishing year.

.. code-block:: python

   embedding.feed_author_profile(
      skip_,
      limit_)

   embedding.author_profile2papers(
      skip_,
      limit_)


