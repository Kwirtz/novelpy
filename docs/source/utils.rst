.. _Utils:

Utils
=====

.. _cooc_utils:

cooc_utils
------------

Most indicators hypothesise that new ideas are created by combining already existing ones. They look at the combination of items (Journals cited, keywords used, ...). cooc_utils creates an adjacency matrix that retraces the history of these combinations done in a given year.


.. py:function:: create_cooc(var, sub_var, year_var, collection_name, time_window, dtype = np.uint32, weighted_network = False, self_loop = False, client_name = None, db_name = None)

   Create a co-occurrence matrix of a field (e.g. authors, keywords, ref) by year.
   Matrices are sparse csr and pickled for later usage.

   :param str var: The key of interest in the dict.
   :param str sub_var: Name of the key which holds the ID of the variable of interest.
   :param str year_var: Name of the key whose value is the year of creation of the document.
   :param str collection_name: Name of the collection (either Mongo or Json) where the data is
   :param range time_window: Compute the cooc for the years in range
   :param np.dtype dtype: The dtype for the co-occurence matrix.
   :param str weighted_network: False if you want a combination that appears multiple times in a single paper to be accounted as 1
   :param str self_loop: True if you want the diagonal in the co-occurrence matrix
   :param str client_name: Name of the MongoDB client
   :param str db_name: Name of the MongoDB

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 

.. _embedding:

embedding
------------

In order to use the indicators of Shibayama et al (2021) and the one on authors, it is necessary to embed the title or abstract of the document.


.. py:function:: Embedding(year_variable, id_variable, references_variable, pretrain_path, time_range, title_variable = None, abstract_variable = None, keywords_variable = None, keywords_subvariable = None, abstract_subvariable = None, aut_id_variable = None, aut_pubs_variable = None, client_name = None, db_name = None)

    Compute the semantic centroid for each paper (abstract and title)
    Compute an author profile of embedded articles per year and store it.

   :param str year_variable: Key where value is the year of publication of the document.
   :param str id_variable: Key where value is the document's id.
   :param range time_range: Create the embedding for papers published in the time_range if None it iterates on all available years.
   :param str pretrain_path: path to the pretrain word2vec: 'your/path/to/en_core_sci_lg-0.4.0/en_core_sci_lg/en_core_sci_lg-0.4.0.
   :param str title_variable: Key where value is the document's title.
   :param str abstract_variable: Key where value is the abstract's information for the document.
   :param str abstract_sub_variable: Key inside abstract variable where value is text of the abstract.
   :param str keywords_variable: Key where value is the keywords' information for the document.
   :param str keywords_subvariable: Key inside keywords_variable where value is the actual keyword.
   :param str aut_id_variable: In collection author key where value is the ID of an author.
   :param str aut_pubs_variable: In collection author key where value is the document list for a given author.
   :param str client_name: name of the MongoDB client.
   :param str db_name: name of the MongoDB

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 



.. code-block:: python

   from novelpy.utils.embedding import Embedding

   embedding = Embedding(
         year_variable = 'year',
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

Once this is done you can run the Shibayama et al. [2021] :cite:p:`shibayama2021measuring` indicator.


.. _plot_dist:

plot_dist
------------

Once you have computed multiple indicators, you can plot the distribution for a document of the novelty score for combinations of items in a document.


.. py:function:: plot_dist(doc_id, doc_year,  id_variable, variables, indicators, time_window_cooc = None, n_reutilisation = None, embedding_entities = None, shibayma_per = 10, client_name = None, db_name = None)

   Plot the distribution of novelty score for combinations of items in a document

   :param str/int doc_id: The id of the document you want the distribution.
   :param int doc_year: Year of creation of the document.
   :param str id_variable: Name of the key that contains the ID of the doc   
   :param list variables: List of variables you want the distribution of (e.g. ["references", "meshterms"])
   :param list indicators: List of indicators name you want the distribution of(e.g ["foster","wang"])
   :param list of int time_window_cooc: List of parameters you want the distribution of, parameters used in wang (e.g [3,5])
   :param list n_reutilisation: List of parameters you want the distribution of, parameter used in wang (e.g [1,2])
   :param list embedding_entities: List of entities you want the distribution of, parameters used in shibayama (e.g ["title","abstract"])
   :param int shibayma_per: In shibayama they compared different percentile for the novelty score of each combination (int between 0 and 100)
   :param str client_name: Name of the MongoDB client
   :param str db_name: Name of the MongoDB

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 


.. _novelty_trend:

novelty_trend
------------

Once you have computed multiple indicators, you can plot the trend of each indicator's mean novelty score per year, given the variables and hyperparameters.


.. py:function:: novelty_trend(year_range, variables, indicators, id_variable, time_window_cooc = None, n_reutilisation = None, embedding_entities = None, shibayama_per = 10, client_name = None, db_name = None)

   Plot the novelty trend (mean per year) for an indicator given the variable

   :param range year_range: Get the trend for each year in year_range.
   :param list variables: List of variables you want the novelty trend of (e.g. ["references", "meshterms"]).
   :param list indicators: List of indicators name you want the novelty of(e.g ["foster","wang"]).
   :param str id_variable: Name of the key that contains the ID of the doc.   
   :param list of int time_window_cooc: List of parameters you want the distribution of, parameters used in wang (e.g [3,5]).
   :param list n_reutilisation: List of parameters you want the distribution of, parameter used in wang (e.g [1,2]).
   :param list embedding_entities: List of entities you want the distribution of, parameters used in shibayama (e.g ["title","abstract"]).
   :param int shibayma_per: In shibayama they compared different percentile for the novelty score of each combination (int between 0 and 100).
   :param str client_name: Name of the MongoDB client.
   :param str db_name: Name of the MongoDB.

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 



.. _correlation_indicators:

correlation_indicators
------------

Once you have computed multiple indicators, you can plot the correlation heatmap of the novelty score, either per year or during the whole period, for each indicator, given the variables and hyperparameters.


.. py:function:: correlation_indicators(year_range, variables, indicators, time_window_cooc = None, n_reutilisation = None, embedding_entities = None, shibayama_per = 10, client_name = None, db_name = None)

   Plot the novelty trend (mean per year) for an indicator given the variable

   :param range year_range: Get the trend for each year in year_range.
   :param list variables: List of variables you want the novelty trend of (e.g. ["references", "meshterms"]).
   :param list indicators: List of indicators name you want the novelty of(e.g ["foster","wang"]).
   :param list of int time_window_cooc: List of parameters you want the distribution of, parameters used in wang (e.g. [3,5]).
   :param list n_reutilisation: List of parameters you want the distribution of, parameter used in wang (e.g [1,2]).
   :param list embedding_entities: List of entities you want the distribution of, parameters used in shibayama (e.g. ["title","abstract"]).
   :param int shibayma_per: In shibayama they compared different percentile for the novelty score of each combination (int between 0 and 100).
   :param str client_name: Name of the MongoDB client.
   :param str db_name: Name of the MongoDB.

   :return: 
   
   :raises ValueError: 
   :raises TypeError: 
