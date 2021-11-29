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

The goal of the measure proposed by Uzzi et al. [2013] is to compare an observed network (hear co-occurrence matrix) with a random network where edges are rearranged randomly at a year level.  They call it "Atypicality".

To run "Atypicality" you'll need the co-occurence matrix of the focal year but also the information about items to create this random network



.. py:function:: Uzzi2013(collection_name, id_variable, year_variable, variable, sub_variable, focal_year, client_name = None, db_name = None, nb_sample = 20)

   Create co-occurence matrix 

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


In order to run Atypicality you first need to create a co-occurence matrix, read more in :ref:`Usage` and :ref:`Utils:cooc_utils`

.. code-block:: python

   import novelpy
   import tqdm

   for focal_year in tqdm.tqdm(range(2000,2016), desc = "Computing indicator for window of time"):
       Uzzi = novelpy.indicators.Uzzi2013(collection_name = 'meshterms_sample',
                                              id_variable = 'PMID',
                                              year_variable = 'year',
                                              variable = "a06_meshheadinglist",
                                              sub_variable = "descUI",
                                              focal_year = focal_year)
       Uzzi.get_indicator()

Foster et al. [2015]
~~~~~~~~~~~~~~~~~~~~~~

Foster et al. [2015] define novelty as an iter-community combination. Basically a combination has a novelty score of 1 if the two items are not in the same community. The original idea was using the infomap community detection algorithm. Most recently Foster et al [2021] used the louvain algorithm. Currently only Louvain is supporte see the :ref:`roadmap` section

The Foster algorithm

.. py:function:: Foster2015(current_adj, year, variable, community_algorithm)

   Create co-occurence matrix 

   :param str scipy.sparse.csr.csr_matrix: Cooc matrix for the year
   :param int year: The focal year (only for saving)
   :param str variable: Variable of interest (Only for saving)
   :param str community_algorithm: The name of the community algorithm. Only supports "Louvain" for the moment

   :return: 
   :raises ValueError: 
   :raises TypeError: 

.. code-block:: python
   # Most (if not every) indicator works on a given year, here we want novelty for papers done in 2000
   focal_year = 2000

   # Class that helps you load, save and compute scores 
   companion = novelpy.utils.run_indicator_tools.create_output(
               collection_name = 'meshterms_sample',
               var = 'c04_referencelist',
               sub_var = "item",
               var_id = 'PMID',
               var_year = 'year',
               indicator = "foster",
               focal_year = focal_year)
   
   # Load cooc, and items 
   companion.get_data()
   
   # For Foster 2015 you only need the co-occurrence matrix

   Foster = novelpy.indicators.Foster2015(current_adj=companion.current_adj,
                                          year = focal_year,
                                          variable = "a06_meshheadinglist",
                                          community_algorithm = "Louvain")
   Foster.get_indicator()
   
   # Iterate through the papers from the focal year and attribute a Novelty score to them
   companion.update_paper_values()


Lee et al. [2015]
~~~~~~~~~~~~~~~~~~~~~~

Wang et al. [2017]
~~~~~~~~~~~~~~~~~~~~~~

Shibayama et al. [2021]
~~~~~~~~~~~~~~~~~~~~~~

Disruptiveness indicators
----------------

Wu et al. [2019]
~~~~~~~~~~~~~~~~~~~~~~

Bu et al. [2019]
~~~~~~~~~~~~~~~~~~~~~~



List of Disruptiveness indicators we currently support:
