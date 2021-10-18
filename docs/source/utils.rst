Utils
=====

.. _cooc_utils:

cooc_utils
------------

Most of the indicators are based on the idea that new ideas are created by combining already existing ones. In that end they look at the combination of items (Journals cited, keywords used, ...). cooc_utils creates an adjacency matrix that retraces the historic of these combination done in a given year:


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


