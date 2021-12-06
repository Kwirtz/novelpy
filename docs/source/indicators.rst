.. _Indicators:

Indicators
=====

.. _Novelty:
.. _Dirsuptiveness:

Novelty indicators
------------

Here are the novelty indicators we currently support:

Uzzi et al. [2013]
~~~~~~~~~~~~~~~~~~~~~~

The goal of the measure proposed by Uzzi et al. [2013] :cite:p:`uzzi2013atypical` is to compare an observed network (hear co-occurrence matrix) with a random network where edges are rearranged randomly at a year level.  They call it "Atypicality".

.. image:: img/uzzi.png
   :width: 450
   :align: center

.. image:: img/uzzi2.png
   :width: 250
   :align: center

.. py:function:: Uzzi2013(collection_name, id_variable, year_variable, variable, sub_variable, focal_year, client_name = None, db_name = None, nb_sample = 20)

   Compute novelty score for every paper for the focal_year based on Uzzi et al. 2013 

   :param str collection_name: Name of the collection or the json file containing the data   
   :param str id_variable: Name of the key which value give the identity of the document.
   :param str year_variable: Name of the key which value is the year of creation of the document.
   :param str variable: Name of the key that holds the variable of interest used in combinations.
   :param str sub_variable: Name of the key which holds the ID of the variable of interest.
   :param int focal_year: Calculate the novelty score for every document which has a date of creation = focal_year.
   :param str client_name: Mongo URI if your data is hosted on a MongoDB instead of a JSON file
   :param str db_name: Name of the db
   :param int nb_sample: Number of resample of the co-occurence matrix.

   :return: 

   :raises ValueError: 
   :raises TypeError: 


In order to run Atypicality you first need to create a co-occurence matrix with self-loop = True and weighted_network = True, read more in :ref:`Usage:tutorial` and :ref:`Utils:cooc_utils`

.. code-block:: python

   import novelpy
   import tqdm

   focal_year = 2000
   Uzzi = novelpy.indicators.Uzzi2013(collection_name = 'references_sample',
                                          id_variable = 'PMID',
                                          year_variable = 'year',
                                          variable = "c04_referencelist",
                                          sub_variable = "items",
                                          focal_year = focal_year)
   Uzzi.get_indicator()


Foster et al. [2015]
~~~~~~~~~~~~~~~~~~~~~~

Foster et al. [2015] :cite:p:`foster2015tradition` define novelty as an inter-community combination. A combination has a novelty score of 1 if the two items are not in the same community. The original paper was using the infomap community detection algorithm. Most recently Foster et al [2021] :cite:p:`foster2021surprise` used the louvain algorithm. Currently only Louvain is supported see the :ref:`roadmap` section. The score for a given entity is the proportion of novel combination on the total number of combination.

.. image:: img/foster.png
   :width: 300
   :align: center

.. py:function:: Foster2015(collection_name, id_variable, year_variable, variable, sub_variable, focal_year, client_name = None, db_name = None, community_algorithm = "Louvain")

   Compute novelty score for every paper for the focal_year based on Foster et al. 2015 

   :param str collection_name: Name of the collection or the json file containing the data   
   :param str id_variable: Name of the key which value give the identity of the document.
   :param str year_variable: Name of the key which value is the year of creation of the document.
   :param str variable: Name of the key that holds the variable of interest used in combinations.
   :param str sub_variable: Name of the key which holds the ID of the variable of interest.
   :param int focal_year: Calculate the novelty score for every document which has a date of creation = focal_year.
   :param str client_name: Mongo URI if your data is hosted on a MongoDB instead of a JSON file
   :param str db_name: Name of the db
   :param str community_algorithm: The name of the community algorithm to be used.

   :return: 

   :raises ValueError: 

   :raises TypeError: 

In order to run this novelty indicator you first need to create a co-occurence matrix with self-loop = True and weighted_network = True, read more in :ref:`Usage:tutorial` and :ref:`Utils:cooc_utils`

.. code-block:: python

   focal_year = 2000
    
   Foster = novelpy.indicators.Foster2015(collection_name = 'references_sample',
                                          id_variable = 'PMID',
                                          year_variable = 'year',
                                          variable = "c04_referencelist",
                                          sub_variable = "item",
                                          focal_year = focal_year,
                                          community_algorithm = "Louvain")
   Foster.get_indicator()



Lee et al. [2015]
~~~~~~~~~~~~~~~~~~~~~~

Lee et al. [2015] :cite:p:`lee2015creativity` compare the observed number of combination with the theoretical number of combination between two items. The higher (lower) the observed (theoretical) number of combination the more novel is the paper. They call this measure "commonness".

.. image:: img/lee.png
   :width: 250
   :align: center

.. py:function:: Lee2015(collection_name, id_variable, year_variable, variable, sub_variable, focal_year, client_name = None, db_name = None)

   Compute novelty score for every paper for the focal_year based on Foster et al. 2015 

   :param str collection_name: Name of the collection or the json file containing the data   
   :param str id_variable: Name of the key which value give the identity of the document.
   :param str year_variable: Name of the key which value is the year of creation of the document.
   :param str variable: Name of the key that holds the variable of interest used in combinations.
   :param str sub_variable: Name of the key which holds the ID of the variable of interest.
   :param int focal_year: Calculate the novelty score for every document which has a date of creation = focal_year.
   :param str client_name: Mongo URI if your data is hosted on a MongoDB instead of a JSON file
   :param str db_name: Name of the db

   :return: 

   :raises ValueError: 

   :raises TypeError: 

In order to run "commonness" you first need to create a co-occurence matrix with self-loop = True and weighted_network = True, read more in :ref:`Usage:tutorial` and :ref:`Utils:cooc_utils`

.. code-block:: python

   import novelpy

   focal_year = 2000

   Lee = novelpy.indicators.Lee2015(collection_name = 'references_sample',
                                          id_variable = 'PMID',
                                          year_variable = 'year',
                                          variable = "c04_referencelist",
                                          sub_variable = "item",
                                          focal_year = focal_year)
   Lee.get_indicator()

Wang et al. [2017]
~~~~~~~~~~~~~~~~~~~~~~

Wang et al. [2017] :cite:p:`wang2017bias` proposed a measure of difficulty on pair of references that were never made before, but that are reused after the given publication’s year (Scholars do not have to cite directly the paper that create the combination but only the combination itself). The idea is to compute the cosine similarity for each journal combination based on their co-citation profile b years before t.

.. image:: img/wang.png
   :width: 600
   :align: center

.. py:function:: Wang2017(collection_name, id_variable, year_variable, variable, sub_variable, focal_year, time_window_cooc, n_reutilisation,client_name = None, db_name = None)

   Compute novelty score for every paper for the focal_year based on Uzzi et al. 2013 

   :param str collection_name: Name of the collection or the json file containing the data   
   :param str id_variable: Name of the key which value give the identity of the document.
   :param str year_variable: Name of the key which value is the year of creation of the document.
   :param str variable: Name of the key that holds the variable of interest used in combinations.
   :param str sub_variable: Name of the key which holds the ID of the variable of interest.
   :param int focal_year: Calculate the novelty score for every document which has a date of creation = focal_year.
   :param int time_window_cooc: Calculate the novelty score using the accumulation of the co-occurence matrix between focal_year-time_window_cooc and focal_year.
   :param int n_reutilisation: Check if the combination is reused n_reutilisation year after the focal_year
   :param str client_name: Mongo URI if your data is hosted on a MongoDB instead of a JSON file
   :param str db_name: Name of the db


   :return: 

   :raises ValueError: 
   :raises TypeError: 

In order to run the indicator you first need to create a co-occurence matrix with self-loop = True and weighted_network = True, read more in :ref:`Usage:tutorial` and :ref:`Utils:cooc_utils`

.. code-block:: python

   import novelpy

   focal_year = 2000

   Wang = novelpy.indicators.Wang2017(collection_name = 'meshterms_sample',
                                          id_variable = 'PMID',
                                          year_variable = 'year',
                                          variable = "a06_meshheadinglist",
                                          sub_variable = "descUI",
                                          focal_year = focal_year,
                                          time_window_cooc = 3,
                                          n_reutilisation = 1)
   Wang.get_indicator()
    


Shibayama et al. [2021]
~~~~~~~~~~~~~~~~~~~~~~

:cite:p:`shibayama2021measuring`



.. image:: img/shibayama.png
   :width: 300
   :align: center

.. py:function:: Shibayama2021(collection_name, id_variable, year_variable, ref_variable, entity, focal_year, client_name = None, db_name = None)

   Compute novelty score for every paper for the focal_year based on Uzzi et al. 2013 

   :param str collection_name: Name of the collection or the json file containing the data   
   :param str id_variable: Name of the key which value give the identity of the document.
   :param str year_variable: Name of the key which value is the year of creation of the document.
   :param str ref_variable: variable name for embedded representation of references.
   :param list entity: list of variables to use, 'title_embedding' or 'abstract_embedding' or both.
   :param int focal_year: Calculate the novelty score for every document which has a date of creation = focal_year.
   :param str client_name: Mongo URI if your data is hosted on a MongoDB instead of a JSON file
   :param str db_name: Name of the db


   :return: 

   :raises ValueError: 
   :raises TypeError: 


In order to run the indicator you first need to embed articles using the function "Embedding",
 read more in :ref:`Usage:tutorial` and :ref:`Utils:embedding`

.. code-block:: python

   import novelpy

   focal_year = 2000

   shibayama = novelpy.indicators.Shibayama2021(
	collection_name = 'articles',
	id_variable = 'PMID',
	year_variable = 'year',
	ref_variable = 'refs_embedding',
  	entity = ['title_embedding','abstract_embedding'],
  	focal_year = focal_year)

   shibayama.get_indicator()

Disruptiveness indicators
----------------

Wu et al. [2019]/  Bornmann et al. 2019/ Bu et al. [2019]
~~~~~~~~~~~~~~~~~~~~~~

:cite:p:`wu2019solo` & :cite:p:`bornmann1911disruption`

:cite:p:`bu2019multi`

All indicators at computed at the same time, one just need to run the following command and iterate over the citation database:

.. py:function:: Disruptiveness(client_name = None, db_name = None, collection_name, focal_year, id_variable, refs_list_variable, year_variable)

   Compute several indicators of disruptiveness studied in Bornmann and Tekles (2020) and in Bu et al. (2019)

   :param str collection_name: Name of the collection or the json file containing the data   
   :param str id_variable: Name of the key which value give the identity of the document.
   :param str year_variable: Name of the key which value is the year of creation of the document.
   :param str variable: Name of the key that holds the variable of interest used in combinations.
   :param str sub_variable: Name of the key which holds the ID of the variable of interest.
   :param int focal_year: Calculate the novelty score for every document which has a date of creation = focal_year.
   :param str client_name: Mongo URI if your data is hosted on a MongoDB instead of a JSON file
   :param str db_name: Name of the db


.. code-block:: python

   disruptiveness = novelpy.Disruptiveness(
      client_name = pars['client_name'], 
      db_name =  'novelty',
      collection_name = 'citation_network',
      focal_year = focal_year,
      id_variable = 'PMID',
      refs_list_variable ='refs_pmid_wos',
      year_variable = 'year')

   disruptiveness.get_indicators(parallel = True)


.. bibliography::