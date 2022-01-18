import os
import json
import tqdm
import pymongo
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from collections import defaultdict

class plot_dist:
    
    def __init__(self,
                 doc_id,
                 doc_year,
                 variables,
                 id_variable,
                 indicators,
                 time_window_cooc = None,
                 n_reutilisation = None,
                 embedding_entities = None,
                 shibayma_per = 10,
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
        variables : str/list of str
            Plot the distribution for a specific unit of knowledge. 
            If arg is a list draw the different distribution on the same plot 
        id_variable : str
            Name of the key which value give the identity of the document.
        indicators : str/ list of str
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
        self.variables = variables
        self.id_variable = id_variable
        self.indicators = indicators
        self.embedding_entities = embedding_entities
        self.shibayma_per = shibayma_per
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        
        if not isinstance(variables, list) or not isinstance(indicators, list):
            raise ValueError('indicator and variable should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list for Wang et al')
        if "shibayama" in self.indicators:
            if not isinstance(embedding_entities, list):
                raise ValueError('embedding_entities should be a list for Shibayama et al.')
                
        self.df = pd.DataFrame(columns = ["Scores","Variable","Indicator"])
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()

    def get_info_mongo(self):                
        self.client = pymongo.MongoClient(self.client_name)
        self.db = self.client[self.db_name]
        self.collection = self.db["output"]
        self.doc = self.collection.find_one({self.id_variable:self.doc_id,"year":self.doc_year})
        
        self.line_position = []
        for indicator in self.indicators:
            for variable in self.variables:
                if indicator == 'wang':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [variable + "_" + str(time) + "_" + str(reu), indicator]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)
                        self.line_position.append(self.doc[key_name]["score"]["novelty"])
                elif indicator =="shibayama":
                    key_name = "shibayama"
                    for embedding_entity in self.embedding_entities:
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [embedding_entity, indicator]   
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)
                        self.line_position.append(float(np.percentile(a = self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                      q = self.shibayma_per)))
                else:
                    key_name = variable + "_" + indicator
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [variable, indicator]
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    self.line_position.append(self.doc[key_name]["score"]["novelty"])

    def get_info_json(self):
        self.line_position = []
        for indicator in self.indicators:
            for variable in self.variables:
                if indicator == 'wang':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                        self.path_doc= "Result/{}/{}/{}".format(indicator, variable + "_" + str(time) + "_" + str(reu) ,self.doc_year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            self.docs = json.load(read_file)
                        try:
                            self.doc = [doc for doc in self.docs if doc[self.id_variable] == self.doc_id][0]
                        except:
                            raise Exception("No object with the ID {} or not enough combinations to have a score on entity {} and indicator {}".format(self.doc_id,variable,indicator))
                        self.line_position.append(self.doc[key_name]["score"]["novelty"])
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [variable + "_" + str(time) + "_" + str(reu), indicator]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)                           
                elif indicator =="shibayama":
                    key_name = "shibayama"
                    self.path_doc= "Result/{}/{}".format(indicator,self.doc_year)
                    with open(self.path_doc + ".json", "r") as read_file:
                        self.docs = json.load(read_file)
                    try:
                        self.doc = [x for x in self.docs if x[self.id_variable] == self.doc_id][0]                    
                    except:
                            raise Exception("No object with the ID {} or not enough combinations to have a score on entity {} and indicator {}".format(self.doc_id,variable,indicator))
                    for embedding_entity in self.embedding_entities:
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [embedding_entity, indicator]   
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)
                        self.line_position.append(float(np.percentile(a = self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                      q = self.shibayma_per)))    
                else:                        
                    key_name = variable + "_" + indicator
                    self.path_doc= "Result/{}/{}/{}".format(indicator, variable,self.doc_year)
                    with open(self.path_doc + ".json", "r") as read_file:
                        self.docs = json.load(read_file)
                    try:
                        self.doc = [x for x in self.docs if x[self.id_variable] == self.doc_id][0]
                    except:
                            raise Exception("No object with the ID {} or not enough combinations to have a score on entity {} and indicator {}".format(self.doc_id,variable,indicator))
                    self.line_position.append(self.doc[key_name]["score"]["novelty"])
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [variable, indicator]
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
        n = 0
        z = 0
        for (i,j,k), data in g.facet_data():
            if data.empty:
                ax = g.facet_axis(i, j)
                ax.set_axis_off()
                z += 1
            else:
                ax = g.axes.flat[z]
                if self.line_position[n] != None:
                    ax.axvline(x=self.line_position[n], color='r', linestyle='--', linewidth = 1)
                z += 1
                n += 1
        """
        for ax, pos in zip(g.axes.flat, self.line_position):
            ax.axvline(x=pos, color='r', linestyle='--', linewidth = 1)
        """
        for i in range(len(self.variables)):
            g.axes[-1,i].set_xlabel('Combination scores')
        plt.legend(handles=[plt.Line2D([], [], color="red", linestyle="--", linewidth = 1, label="Novelty score")])

class novelty_trend:

    def __init__(self,
                 year_range,
                 variables,
                 indicators,
                 id_variable,
                 time_window_cooc = None,
                 n_reutilisation = None,
                 embedding_entities = None,
                 shibayma_per = 10,
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
        self.id_variable = id_variable
        self.variables = variables
        self.indicators = indicators
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        self.embedding_entities = embedding_entities
        self.shibayma_per =  shibayma_per
        
        if not isinstance(variables, list) or not isinstance(indicators, list):
            raise ValueError('indicator and variable should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list')
        if "shibayma" in self.indicators:
            if not isinstance(self.embedding_entites, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list')
                
        self.df = pd.DataFrame(columns = ["Score_mean","Variable","Indicator","Year"])
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()
    

    def get_info_mongo(self):                
        self.client = pymongo.MongoClient(self.client_name)
        self.db = self.client[self.db_name]
        self.collection = self.db["output"]
        
        for indicator in self.indicators:
            for variable in self.variables:
                if indicator == 'wang':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                        for year in self.year_range:
                            docs = self.collection.find({"year":year})
                            score_list = []
                            for doc in docs:
                                try:
                                    score_list.append(doc[key_name]["score"]["novelty"])   
                                except:
                                    continue
                            df_temp = pd.DataFrame([np.mean(score_list)], columns=["Score_mean"])
                            df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [variable + "_" + str(time) + "_" + str(reu), indicator, year]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)    
                elif indicator =="shibayama":
                    key_name = "shibayama"
                    for embedding_entity in self.embedding_entities:
                        for year in self.year_range:
                                docs = self.collection.find({"year":year})
                                score_list = []
                                for doc in docs:
                                    try:
                                        score_list.append(float(np.percentile(a = doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                      q = self.shibayama_per)))
                                    except:
                                        continue
                                df_temp = pd.DataFrame([np.mean(score_list)], columns=["Score_mean"])
                                df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [embedding_entity, indicator, year]
                                self.df = pd.concat([self.df,df_temp], ignore_index=True)             
                else:
                    key_name = variable + "_" + indicator
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [variable, indicator]
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    
    def get_info_json(self):
        for indicator in self.indicators:
            for variable in self.variables:
                if indicator == 'wang':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                        for year in self.year_range:
                            self.path_doc= "Result/{}/{}/{}".format(indicator, variable + "_" + str(time) + "_" + str(reu) , year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                self.docs = json.load(read_file)
                            score_list = []
                            for doc in self.docs:
                                try:
                                    score_list.append(doc[key_name]["score"]["novelty"])
                                except:
                                    continue
                            df_temp = pd.DataFrame([np.mean(score_list)], columns=["Score_mean"])
                            df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [variable + "_" + str(time) + "_" + str(reu), indicator, year]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)                           
                elif indicator =="shibayama":
                    key_name = "shibayama"
                    for embedding_entity in self.embedding_entities:
                        for year in self.year_range:
                            self.path_doc= "Result/{}/{}".format(indicator, year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                self.docs = json.load(read_file)   
                            score_list = []
                            for doc in self.docs:
                                try:
                                    score_list.append(float(np.percentile(a = doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                      q = self.shibayama_per)))
                                except:
                                    continue
                            df_temp = pd.DataFrame([np.mean(np.ma.masked_invalid(score_list))], columns=["Score_mean"])
                            df_temp['Variable'], df_temp['Indicator'], df_temp["Year"] = [embedding_entity, indicator, year]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)   
                else:                        
                    key_name = variable + "_" + indicator
                    for year in self.year_range:
                        self.path_doc= "Result/{}/{}/{}".format(indicator, variable, year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            self.docs = json.load(read_file)
                        score_list = []
                        for doc in self.docs:
                            score_list.append(doc[key_name]["score"]["novelty"])
                        df_temp = pd.DataFrame([np.mean(np.ma.masked_invalid(score_list))], columns=["Score_mean"])
                        df_temp['Variable'], df_temp['Indicator'], df_temp["Year"] = [variable, indicator, year]
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
        for (i,j,k), data in g.facet_data():
            if data.empty:
                ax = g.facet_axis(i, j)
                ax.set_axis_off()



class correlation_indicators:
    
    def __init__(self,
                 year_range,
                 variables,
                 indicators,
                 time_window_cooc = None,
                 n_reutilisation = None,
                 embedding_entities = None,
                 shibayama_per = 10,
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
        self.variables = variables
        self.indicators = indicators
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        self.embedding_entities = embedding_entities
        self.shibayama_per = shibayama_per
        
        if not isinstance(variables, list) or not isinstance(indicators, list):
            raise ValueError('indicator and variable should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list')
        
        self.corr = defaultdict(dict)
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()
    
    def get_info_mongo(self):
        pass
    
    def get_info_json(self):
        for indicator in self.indicators:
            for variable in self.variables:
                if indicator == 'wang':
                    for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                        key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                        for year in self.year_range:
                            self.path_doc= "Result/{}/{}/{}".format(indicator, variable + "_" + str(time) + "_" + str(reu) , year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                self.docs = json.load(read_file)
                            score_list = []
                            for doc in self.docs:
                                try:
                                    score_list.append(doc[key_name]["score"]["novelty"])
                                except:
                                    continue
                            self.corr[year][key_name] = score_list                  
                elif indicator =="shibayama":
                    key_name = "shibayama"
                    for embedding_entity in self.embedding_entities:
                        for year in self.year_range:
                            self.path_doc= "Result/{}/{}".format(indicator, year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                self.docs = json.load(read_file)   
                            score_list = []
                            for doc in self.docs:
                                try:
                                    score_list.append(float(np.percentile(a = doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                      q = self.shibayama_per)))
                                except:
                                    continue
                            self.corr[year][key_name + "_" + embedding_entity] = score_list 
                else:                        
                    key_name = variable + "_" + indicator
                    for year in self.year_range:
                        self.path_doc= "Result/{}/{}/{}".format(indicator, variable, year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            self.docs = json.load(read_file)
                        score_list = []
                        for doc in self.docs:
                            score_list.append(doc[key_name]["score"]["novelty"])
                        self.corr[year][key_name] = score_list 
        for year in self.year_range:
            self.corr[year] = pd.DataFrame.from_dict(self.corr[year], orient='index').T
    
    def correlation_heatmap(self, log = False, per_year = True):

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
        if per_year == True:
            for year in self.year_range:
                plt.figure()
                cleaned_corr = self.corr[year][~self.corr[year].isin([np.nan, np.inf, -np.inf]).any(1)]
                sns.heatmap(cleaned_corr.corr())
        else:
            cleaned_corr = pd.DataFrame()
            for year in self.year_range:
                cleaned_corr = pd.concat([cleaned_corr, self.corr[year][~self.corr[year].isin([np.nan, np.inf, -np.inf]).any(1)]], ignore_index=True)
            sns.heatmap(cleaned_corr.corr())
                        
