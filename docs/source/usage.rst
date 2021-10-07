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

The package currently supports JSON files which should be located in Data/docs or a MongoDB input. Here's a typical starting folder structure to run novelpy if you use JSON:

project
├── demo.py
├── Data          
│   ├── docs
         ├ authors.json
         ├ references.json
         └ meshterms.json

Depending on what kind of indicator you are running, you will need different kind of input (For example for Uzzi et al.(2013) you only need references.json).
We intend to automatize the process with well known Databases (Web of science, arxiv, Pubmed Knowlede graph, ...). Please look into the :ref:`roadmap` section
If you want to use your own data, please look into the :ref:`sample` made available to have a clear idea of the parsing we expect.

.. _sample:
Sample
----------------

We made available a small sample of data so you can get familiar with the package with well formated data. To get this sample run the following code in your project folder:

>>> from novelpy.utils.get_sample import download_sample
>>> download_sample()

Or if you want to test the package with MongoDB run:

>>> download_sample(mongo=True)


This will give you the file as seen in :ref:`format`


