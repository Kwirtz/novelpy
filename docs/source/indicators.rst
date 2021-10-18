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



.. py:function:: Atypicality(var, var_year, focal_year, current_items, unique_items, true_current_adj_freq)

   Create co-occurence matrix 

   :param str var: The key of interest in the dict
   :param str var_year: The key that gives the year of the paper
   :param str focal_year: Name of the collection (either Mongo or Json) where the data is
   :param dict current_items: dict with id as key and item info as value.
   :param dict unique_items: dict structured this way name:index, file from the name2index.p generated with the cooccurrence matrices.
   :param scipy.sparse.csr.csr_matrix true_current_adj_freq: current adjacency matrix.

   :return: 
   :raises ValueError: 
   :raises TypeError: 

.. code-block:: python
   # Most (if not every) indicator works for a given year, here we want novelty for papers done in 2000
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
