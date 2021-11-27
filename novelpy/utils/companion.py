import os
import json
import tqdm
import pymongo
import numpy as np
import pandas as pd
import seaborn as sns
from collections import defaultdict
import matplotlib
import matplotlib.pyplot as plt

class plot_dist:
    
    def __init__(self,
                 doc_id,
                 doc_year,
                 variable,
                 indicator,
                 time_window_cooc = None,
                 n_reutilisation = None,
                 client_name = None,
                 db_name = None):
        """
        Description
        -----------
        Class that returns the distribution of novelty scores for a given paper and for a list of indicator or variable
        
        Parameters
        ----------


        doc_id : int
            The id of the entity (paper/patent/others) you want to plot the distribution.
        doc_year : int
            The year of the entity (paper/patent/others) you want to plot the distribution.
        variable : str/list of str
            Plot the distribution for a specific unit of knowledge. 
            If arg is a list draw the different distribution on the same plot 
        indicator : str/ list of str
            Plot the distribution for a specific indicator.
            If arg is a list draw the different distribution on the same plot 
        client_name : str, optional
            client name. The default is None.
        db_name : str, optional
            db name. The default is None.    
            
        Returns
        -------
        None.
    
        """
        
        self.client_name = client_name
        self.db_name = db_name
        self.doc_id = doc_id
        self.doc_year = doc_year
        self.variable = variable
        self.indicator = indicator
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        
        if not isinstance(variable, list) or not isinstance(indicator, list):
            raise ValueError('indicator and variable should be a list')
        if "novelty" in self.indicator:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list')
                
        self.df = pd.DataFrame(columns = ["Scores","Variable","Indicator"])
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()

    def get_info_mongo(self):                
        self.client = pymongo.MongoClient(client_name)
        self.db = self.client[db_name]
        self.collection = self.db["output"]
        self.doc = self.collection.find_one({"PMID":self.doc_id,"year":self.doc_year})
        for x in self.indicator:
            for y in self.variable:
                if x == 'novelty':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = y + "_" + x + "_" + str(self.time_window_cooc) + "y_" + str(self.n_reutilisation) + "reu"
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [y + "_" + str(self.time_window_cooc) + "y_" + str(self.n_reutilisation) + "reu", x]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)                           
                else:
                    key_name = y + "_" + x
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [y, x]
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    
    def get_info_json(self):
        self.line_position = []
        for x in self.indicator:
            for y in self.variable:
                if x == 'novelty':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = y + "_" + x + "_" + str(time) + "y_" + str(reu) + "reu"
                        self.path_doc= "Result/{}/{}/{}".format(x, y + "_" + str(time) + "y_" + str(reu) + "reu" ,self.doc_year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            self.docs = json.load(read_file)
                        self.doc = [x for x in self.docs if x['PMID'] == self.doc_id][0]
                        self.line_position.append(self.doc[key_name]["score"]["novelty"])
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [y + "_" + str(time) + "y_" + str(reu) + "reu", x]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)                           
                else:                        
                    key_name = y + "_" + x
                    self.path_doc= "Result/{}/{}/{}".format(x, y,self.doc_year)
                    with open(self.path_doc + ".json", "r") as read_file:
                        self.docs = json.load(read_file)
                    self.doc = [x for x in self.docs if x['PMID'] == self.doc_id][0]
                    self.line_position.append(self.doc[key_name]["score"]["novelty"])
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [y, x]
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)        
        
    def get_plot_dist(self):

        """
   
        Description
        -----------        
        Returns the distribution of novelty score

        Parameters
        ----------

        Returns
        -------
        plot

        """
        
        legend_patches = matplotlib.patches.Patch(color="red", label="Novelty score", linestyle='--', fill = False)
        g = sns.FacetGrid(self.df, col="Variable", row="Indicator", sharex=False, sharey=False, margin_titles=True)
        g.set_titles('{col_name}')
        g.fig.suptitle('Doc id: {}'.format(self.doc_id))
        g.map(sns.kdeplot, "Scores")
        for ax, pos in zip(g.axes.flat, self.line_position):
            ax.axvline(x=pos, color='r', linestyle='--', linewidth = 1)
        for i in range(len(self.variable)):
            g.axes[-1,i].set_xlabel('Combination scores')
        plt.legend(handles=[plt.Line2D([], [], color="red", linestyle="--", linewidth = 1, label="Novelty score")])

class novelty_trend:

    def __init__(self,
                 year_range,
                 variable,
                 indicator,
                 time_window_cooc = None,
                 n_reutilisation = None,
                 client_name = None,
                 db_name = None):
        """
        Description
        -----------
        Class that returns the distribution of novelty scores for a given paper and for a list of indicator or variable
        
        Parameters
        ----------


        doc_id : int
            The id of the entity (paper/patent/others) you want to plot the distribution.
        doc_year : int
            The year of the entity (paper/patent/others) you want to plot the distribution.
        variable : str/list of str
            Plot the distribution for a specific unit of knowledge. 
            If arg is a list draw the different distribution on the same plot 
        indicator : str/ list of str
            Plot the distribution for a specific indicator.
            If arg is a list draw the different distribution on the same plot 
        client_name : str, optional
            client name. The default is None.
        db_name : str, optional
            db name. The default is None.    
            
        Returns
        -------
        None.
    
        """
        
        self.client_name = client_name
        self.db_name = db_name
        self.year_range = year_range
        self.variable = variable
        self.indicator = indicator
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        
        if not isinstance(variable, list) or not isinstance(indicator, list):
            raise ValueError('indicator and variable should be a list')
        if "novelty" in self.indicator:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list')
                
        self.df = pd.DataFrame(columns = ["Score_mean","Variable","Indicator","Year"])
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()
    

    def get_info_mongo(self):                
        self.client = pymongo.MongoClient(client_name)
        self.db = self.client[db_name]
        self.collection = self.db["output"]
        self.doc = self.collection.find_one({"PMID":self.doc_id,"year":self.doc_year})
        
        for x in self.indicator:
            for y in self.variable:
                if x == 'novelty':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = y + "_" + x + "_" + str(self.time_window_cooc) + "y_" + str(self.n_reutilisation) + "reu"
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [y + "_" + str(self.time_window_cooc) + "y_" + str(self.n_reutilisation) + "reu", x]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)                           
                else:
                    key_name = y + "_" + x
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [y, x]
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    
    def get_info_json(self):
        for x in self.indicator:
            for y in self.variable:
                if x == 'novelty':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = y + "_" + x + "_" + str(time) + "y_" + str(reu) + "reu"
                        for year in self.year_range:
                            self.path_doc= "Result/{}/{}/{}".format(x, y + "_" + str(time) + "y_" + str(reu) + "reu" , year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                self.docs = json.load(read_file)
                            score_list = []
                            for doc in self.docs:
                                score_list.append(doc[key_name]["score"]["novelty"])
                            df_temp = pd.DataFrame([np.mean(score_list)], columns=["Score_mean"])
                            df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [y + "_" + str(time) + "y_" + str(reu) + "reu", x,year]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)                           
                else:                        
                    key_name = y + "_" + x
                    for year in self.year_range:
                        self.path_doc= "Result/{}/{}/{}".format(x, y, year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            self.docs = json.load(read_file)
                        score_list = []
                        for doc in self.docs:
                            score_list.append(doc[key_name]["score"]["novelty"])
                        df_temp = pd.DataFrame([np.mean(np.ma.masked_invalid(score_list))], columns=["Score_mean"])
                        df_temp['Variable'], df_temp['Indicator'], df_temp["Year"] = [y, x, year]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)        
        
    def get_plot_trend(self):

        """
   
        Description
        -----------        
        Returns the trend of novelty score

        Parameters
        ----------

        Returns
        -------
        plot

        """
        g = sns.FacetGrid(self.df, col="Variable", row="Indicator", sharex=False, sharey=False, margin_titles=True)
        g.set_titles('{col_name}')
        g.fig.suptitle('Novelty trend')
        g.map(sns.lineplot, "Year", "Score_mean")


class correlation_indicators:
    
    def __init__(self,
                 year_range,
                 variable,
                 indicator,
                 time_window_cooc = None,
                 n_reutilisation = None,
                 client_name = None,
                 db_name = None):
        """
        Description
        -----------
        Class that returns the distribution of novelty scores for a given paper and for a list of indicator or variable
        
        Parameters
        ----------


        doc_id : int
            The id of the entity (paper/patent/others) you want to plot the distribution.
        doc_year : int
            The year of the entity (paper/patent/others) you want to plot the distribution.
        variable : str/list of str
            Plot the distribution for a specific unit of knowledge. 
            If arg is a list draw the different distribution on the same plot 
        indicator : str/ list of str
            Plot the distribution for a specific indicator.
            If arg is a list draw the different distribution on the same plot 
        client_name : str, optional
            client name. The default is None.
        db_name : str, optional
            db name. The default is None.    
            
        Returns
        -------
        None.
    
        """
        
        self.client_name = client_name
        self.db_name = db_name
        self.year_range = year_range
        self.variable = variable
        self.indicator = indicator
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        
        if not isinstance(variable, list) or not isinstance(indicator, list):
            raise ValueError('indicator and variable should be a list')
        if "novelty" in self.indicator:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list')
        
        self.corr = defaultdict(dict)
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()
    
    def get_info_json(self):
        for x in self.indicator:
            for y in self.variable:
                if x == 'novelty':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = y + "_" + x + "_" + str(time) + "y_" + str(reu) + "reu"
                        for year in self.year_range:
                            self.path_doc= "Result/{}/{}/{}".format(x, y + "_" + str(time) + "y_" + str(reu) + "reu" , year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                self.docs = json.load(read_file)
                            score_list = []
                            for doc in self.docs:
                                score_list.append(doc[key_name]["score"]["novelty"])
                            self.corr[year][key_name] = score_list  
                else:                        
                    key_name = y + "_" + x
                    for year in self.year_range:
                        self.path_doc= "Result/{}/{}/{}".format(x, y, year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            self.docs = json.load(read_file)
                        score_list = []
                        for doc in self.docs:
                            score_list.append(doc[key_name]["score"]["novelty"])
                        self.corr[year][key_name] = score_list 
        for year in self.year_range:
            self.corr[year] = pd.DataFrame.from_dict(self.corr[year], orient='index').T
    
    def correlation_heatmap(self, log = False):

        """
   
        Description
        -----------        
        Returns the trend of novelty score

        Parameters
        ----------

        Returns
        -------
        plot

        """
        for year in self.year_range:
            cleaned_corr = self.corr[year][~self.corr[year].isin([np.nan, np.inf, -np.inf]).any(1)]
            sns.heatmap(cleaned_corr.corr())

            
"""
doc_infos = plot_dist(doc_id = 10564583,
                      doc_year = 2000,
                      variable = ["c04_referencelist","a06_meshheadinglist"],
                      indicator = ["foster","commonness"],
                      time_window_cooc = [3],
                      n_reutilisation = [1]
                      )
doc_infos.get_plot_dist()
df = doc_infos.df


trend = novelty_trend(year_range = range(2000,2015,1),
              variable = ["c04_referencelist","a06_meshheadinglist"],
              indicator = ["foster","commonness"],
              time_window_cooc = [3],
              n_reutilisation = [1])

trend.get_plot_trend()
"""

corr = correlation_indicators(year_range = range(2000,2015,1),
              variable = ["c04_referencelist","a06_meshheadinglist"],
              indicator = ["foster","commonness"],
              time_window_cooc = [3],
              n_reutilisation = [1])

corr.correlation_heatmap()
df = corr.corr
sns.heatmap(df[2014].corr())
