.. _Utils:

Utils
=====

.. _cooc_utils:

cooc_utils
------------

Most of the indicators make use of the hypothesis that new ideas are created by combining already existing ones. In that end they look at the combination of items (Journals cited, keywords used, ...). cooc_utils creates an adjacency matrix that retraces the historic of these combination done in a given year.


.. py:function:: create_cooc(var, sub_var, year_var, collection_name, client_name = None, db_name = None, time_window = range(1980,2021), weighted_network = False, self_loop = False)

   Create co-occurence matrix 

   :param str var: The key of interest in the dict.
   :param str sub_var: Name of the key which holds the ID of the variable of interest.
   :param str year_var: Name of the key which value is the year of creation of the document.
   :param str collection_name: Name of the collection (either Mongo or Json) where the data is
   :param str client_name: Name of the MongoDB client
   :param str db_name: Name of the MongoDB
   :param range time_window: Compute the cooc for the years in range
   :param str weighted_network: False if you want a combinaisons that appears multiple time in a single paper to be accounted as 1
   :param str self_loop: True if you want the diagonal in the coocurence matrix

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 

.. _embedding:

embedding
------------

In order to use the indicators of Shibayama et al (2021) and the one on authors, it is necessary to embed the entities first. This function only works via mongo for the moment as it is impractical on large data sets. As these indicators are easily usable with small datasets, a version without mongo will be quickly developed.


.. py:function:: Embedding(year_variable, time_range, id_variable, references_variable, pretrain_path, title_variable, abstract_variable, client_name = None, db_name = None, keywords_variable = None, keywords_subvariable = None, abstract_subvariable = None, id_auth_variable = None, auth_pubs_variable = None)

    - Compute semantic centroid for each paper (abstract and title)
    - Create embedded references profile for each article.
    - Compute an author profile of embedded articles per year and store it for each article.

   :param str var_year: year variable name
   :param str var_id: identifier variable name
   :param str var_auth_id: authors identifer variable name
   :param str pretrain_path: path to the pretrain word2vec: 'your/path/to/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0
   :param str var_title: title variable name
   :param str var_abstract: abstract variable name
   :param str var_keyword: keyword variable name
   :param str subvar_keyword: keyword subvariable name
   :param str client_name: Name of the MongoDB client
   :param str db_name: Name of the MongoDB

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 



.. code-block:: python

   from novelpy.utils.embedding import Embedding

   embedding = Embedding(
         year_variable = 'year',
         time_range = range(2000,2011),
         id_variable = 'PMID',
         references_variable = 'refs_pmid_wos',
         pretrain_path = 'en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0',
         title_variable = 'ArticleTitle',
         abstract_variable = 'a04_abstract',
         abstract_subvariable = 'AbstractText')

The first step is to embed every paper's abstract/title by using ``get_articles_centroid``.

.. code-block:: python

   embedding.get_articles_centroid(
         collection_articles = 'Title_abs_sample',
         collection_embedding = 'embedding')


The second step is to create a list for each articles that contains the embedding of each cited articles.


.. code-block:: python

   embedding.get_references_embbeding(
      from_year = 2000,
      to_year = 2010,
      collection_articles = 'articles',
      collection_embedding = 'articles_embedding',
      collection_ref_embedding = 'references_embedding',
      skip_ = 1,
      limit_ = 0)

Once this is done you can run the Shibayama et al. [2021] :cite:p:`shibayama2021measuring` indicator.


.. _plot_dist:

plot_dist
------------

Once you have computed multiple indicators you can plot the distribution for a document of the novelty score for combinations of items in a document.


.. py:function:: plot_dist(doc_id, doc_year,  id_variable, variables, indicators, time_window_cooc = None, n_reutilisation = None, embedding_entities = None, shibayma_per = 10, client_name = None, db_name = None)

   Plot the distribution of novelty score for combinations of items in a document

   :param str/int doc_id: The id of the document you want the distribution.
   :param int doc_year: Year of creation of the document.
   :param str id_variable: Name of the key that contains the ID of the doc   
   :param list variables: List of variable you want the distribution of (e.g ["references", "meshterms"])
   :param list indicators: List of indicators name you want the distribution of(e.g ["foster","wang"])
   :param list of int time_window_cooc: List of parameters you want the distribution of, parameter used in wang (e.g [3,5])
   :param list n_reutilisation: List of parameters you want the distribution of, parameter used in wang (e.g [1,2])
   :param list embedding_entities: List of entites you want the distribution of, parameter used in shibayama (e.g ["title","abstract"])
   :param int shibayma_per: In shibayama they compared diffenrent percentil for the novelty score of each combination (int between 0 and 100)
   :param str client_name: Name of the MongoDB client
   :param str db_name: Name of the MongoDB

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 


.. _novelty_trend:

novelty_trend
------------

Once you have computed multiple indicators you can plot the trend of the mean novelty score per year for each indicator given the variables and hyper-parameters.


.. py:function:: novelty_trend(year_range, variables, indicators, id_variable, time_window_cooc = None, n_reutilisation = None, embedding_entities = None, shibayama_per = 10, client_name = None, db_name = None)

   Plot the novelty trend (mean per year) for an indicator given the variable

   :param range year_range: Get the trend for each years in year_range.
   :param list variables: List of variable you want the novelty trend of (e.g ["references", "meshterms"]).
   :param list indicators: List of indicators name you want the novelty of(e.g ["foster","wang"]).
   :param str id_variable: Name of the key that contains the ID of the doc.   
   :param list of int time_window_cooc: List of parameters you want the distribution of, parameter used in wang (e.g [3,5]).
   :param list n_reutilisation: List of parameters you want the distribution of, parameter used in wang (e.g [1,2]).
   :param list embedding_entities: List of entites you want the distribution of, parameter used in shibayama (e.g ["title","abstract"]).
   :param int shibayma_per: In shibayama they compared diffenrent percentil for the novelty score of each combination (int between 0 and 100).
   :param str client_name: Name of the MongoDB client.
   :param str db_name: Name of the MongoDB.

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 



.. _correlation_indicators:

correlation_indicators
------------

Once you have computed multiple indicators you can plot the correlation heatmap of the novelty score, either per year or during the whole period, for each indicator given the variables and hyper-parameters.


.. py:function:: correlation_indicators(year_range, variables, indicators, time_window_cooc = None, n_reutilisation = None, embedding_entities = None, shibayama_per = 10, client_name = None, db_name = None)

   Plot the novelty trend (mean per year) for an indicator given the variable

   :param range year_range: Get the trend for each years in year_range.
   :param list variables: List of variable you want the novelty trend of (e.g ["references", "meshterms"]).
   :param list indicators: List of indicators name you want the novelty of(e.g ["foster","wang"]).
   :param list of int time_window_cooc: List of parameters you want the distribution of, parameter used in wang (e.g [3,5]).
   :param list n_reutilisation: List of parameters you want the distribution of, parameter used in wang (e.g [1,2]).
   :param list embedding_entities: List of entites you want the distribution of, parameter used in shibayama (e.g ["title","abstract"]).
   :param int shibayma_per: In shibayama they compared diffenrent percentil for the novelty score of each combination (int between 0 and 100).
   :param str client_name: Name of the MongoDB client.
   :param str db_name: Name of the MongoDB.

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 