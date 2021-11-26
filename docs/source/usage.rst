.. _usage:

Usage
=====

.. _installation:

Installation
------------

To use novelpy, first install it using pip:

.. code-block:: console

   $ pip install novelpy


.. _format:
Format supported
----------------

The package currently supports JSON files which should be located in Data/docs or a MongoDB. Here's a typical starting folder structure to run novelpy if you use JSON:

::


   project
   ├── demo.py
   └── Data   
      └── docs
          ├── authors.json       
          ├── references.json
          └── meshterms.json

| Depending on what kind of indicator you are running, you will need different kind of input (For example for Uzzi et al.(2013) you only need references.json). 
|
| We intend to automatize the process with well known Databases (Web of science, arxiv, Pubmed Knowlede graph, ...). Look into the :ref:`roadmap` section to learn
| more about future implementation.
|
| If you want to use your own data, please look into the Sample section below.

.. _sample:
Sample
----------------

We made available a small sample of data so you can get familiar with the package with well formated data. To get this sample run the following code in your project folder:

>>> from novelpy.utils.get_sample import download_sample
>>> download_sample()

| This will give you the file as seen in :ref:`format`_. Read more about this sample structure `here <https://github.com/Kwirtz/data_sample/tree/main/novelpy>`_.
| Or if you want to test the package with MongoDB you can run the following which will create a database "novelty_sample_test" with everything needed:

>>> download_sample(client_name="mongodb://localhost:27017")


.. _tutorial:
Tutorial
----------------

This tutorial suppose you use the sample made available above. Make sure you run the code in the "project" folder

Here's a short implementation to run Foster et al.(2015) novelty indicator. Some indicators available are based on the idea that new knowledge is created by combining already existing pieces of knowledge. Because of this you will require co-occurrence matrices (Refer to our paper novelpy to learn more about the methodology used). We made it so the co-occurrence matrices are saved, so you just have to run the following once:

.. code-block:: python
   
   import novelpy

   ref_cooc = novelpy.utils.cooc_utils.create_cooc(
                    collection_name = "references_sample", 
                    year_var="year",
                    var = "c04_referencelist",
                    sub_var = "item",
                    weighted_network = True, self_loop = True)

   ref_cooc.main()


| If you use MongoDB backend make sure to use the client_name and db_name arguments (:ref:`Utils`).
| Once the co-occurrence matrices are done you should have a new folder "cooc". Depending on which co-occurrence matrices you runned you will have different folder. In the tutorial case we wanted the co-occurrence matrix of journals cited per paper.

::


   project
   ├── demo.py
   └── Data   
      ├── docs
      │   ├── authors.json       
      │   ├── references.json
      │   └── meshterms.json
      │ 
      └── cooc
         └── c04_referencelist
             └── weighted_network_self_loop.p
        


| Read more on the create_cooc function here :ref:`Utils`
| Now you can run the Foster et al. (2015) indicator

.. code-block:: python

   import novelpy

   # Most (if not every) indicator works for a given year, here we want novelty for papers done in 2000
   focal_year = 2000


   Foster = novelpy.indicators.Foster2015(collection_name = 'references_sample',
                                          id_variable = 'PMID',
                                          year_variable = 'year',
                                          variable = "c04_referencelist",
                                          sub_variable = "item",
                                          focal_year = focal_year,
                                          community_algorithm = "Louvain")
   Foster.get_indicator()
    

Now you should have one more folder "Results" with a json for the focal year with the results. 

::


   project
   ├── demo.py
   ├── Data   
   │  ├── docs
   │  │   ├── authors.json       
   │  │   ├── references.json
   │  │   └── meshterms.json
   │  │ 
   │  └── cooc
   │     └── c04_referencelist
   │         └── weighted_network_self_loop.p
   │    
   └── Results
      └── foster
         └── c04_referencelist

| You can iterate through multiple years just by replacing the focal year by a range and a for loop
| More info and demonstration are given in the section :ref:`Indicators`.

| Some pre-build functions can help you perform your analysis by getting the novelty score of a document, plotting the distribution or do a correlation analysis

.. code-block:: python
   
   # Get distribution for paper with id 10564583
   import novelpy

   dist = novelpy.utils.plot_dist(doc_id = 10564583,
                         doc_year = 2000,
                         variable = ["c04_referencelist"],
                         indicator = ["foster"]
                         )
   dist.get_plot_dist()
   
   # The data used for the plot can be found in dist.df

.. image:: img/dist.png
   :width: 600

.. code-block:: python
   
   # A more complex example
   import novelpy

   dist = novelpy.utils.plot_dist(doc_id = 10564583,
                         doc_year = 2000,
                         variable = ["c04_referencelist","a06_meshheadinglist"],
                         indicator = ["foster","commonness"],
                         )
   dist.get_plot_dist()

.. image:: img/dist_complex.png
   :width: 600

.. code-block:: python

   trend = novelpy.utils.novelty_trend(year_range = range(2000,2015,1),
                 variable = ["c04_referencelist","a06_meshheadinglist"],
                 indicator = ["foster","commonness"],
                 time_window_cooc = [3],
                 n_reutilisation = [1])

   trend.get_plot_trend()

.. image:: img/trend.png
   :width: 600

.. code-block:: python
   corr = correlation_indicators(year_range = range(2000,2015,1),
                 variable = ["c04_referencelist","a06_meshheadinglist"],
                 indicator = ["foster","commonness"],
                 time_window_cooc = [3],
                 n_reutilisation = [1])

   corr.correlation_heatmap()

.. image:: img/heatmap.png
   :width: 600