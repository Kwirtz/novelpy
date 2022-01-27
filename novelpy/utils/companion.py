import os
import json
import tqdm
import math
import pymongo
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.gridspec as gridspec



class plot_dist:
    
    def __init__(self,
                 doc_id,
                 doc_year,
                 id_variable,
                 indicators,
                 variables = [],
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
        
        if not isinstance(indicators, list):
            raise ValueError('indicators should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list for Wang et al')
        if "shibayama" in self.indicators:
            if not isinstance(embedding_entities, list):
                raise ValueError('embedding_entities should be a list for Shibayama et al.')
        else:
            if not isinstance(variables, list):
                raise ValueError('variables should be a list')
                
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
            if indicator =="shibayama":
                key_name = "shibayama"
                for embedding_entity in self.embedding_entities:
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [embedding_entity, indicator]   
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    self.line_position.append(float(np.percentile(a = self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayma_per)))
            elif self.variables:
                for variable in self.variables:
                    if indicator == 'wang':
                        for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                            key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                            df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                            df_temp['Variable'], df_temp['Indicator'] = [variable, indicator + "_" + str(time) + "_" + str(reu)]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)
                            self.line_position.append(self.doc[key_name]["score"]["novelty"])
                    else:
                        key_name = variable + "_" + indicator
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [variable, indicator]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)
                        self.line_position.append(self.doc[key_name]["score"]["novelty"])

    def get_info_json(self):
        self.line_position = []
        for indicator in self.indicators:
            if indicator =="shibayama":
                key_name = "shibayama"
                self.path_doc= "Result/{}/{}".format(indicator,self.doc_year)
                with open(self.path_doc + ".json", "r") as read_file:
                    self.docs = json.load(read_file)
                try:
                    self.doc = [x for x in self.docs if x[self.id_variable] == self.doc_id][0]                    
                except:
                    raise Exception("No object with the ID {} or not enough combinations to have a score on entity {} and indicator {}".format(self.doc_id, self.embedding_entities[0],indicator))
                for embedding_entity in self.embedding_entities:
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [embedding_entity, indicator]   
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    self.line_position.append(float(np.percentile(a = self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayma_per)))    
            elif self.variables:
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
                            df_temp['Variable'], df_temp['Indicator'] = [variable, indicator + "_" + str(time) + "_" + str(reu)]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)                           
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
        if "shibayama" in self.indicators and len(self.indicators) > 2:
            grid_spec_col = len(self.indicators) - 1
        grid_spec_row = len(set(self.df["Variable"]))
        
        fig = plt.figure(figsize=(24, 16))
        gs = gridspec.GridSpec(grid_spec_row, grid_spec_col)
        
        n_indic = 0
        n_lines = 0
        for indicator in self.indicators:
            if indicator == "shibayama":
                if len(self.indicators) > 1:
                    starting_row = int(grid_spec_row/2)
                    starting_col = int(grid_spec_col/2)
                    if starting_row % 1 != 0:
                        starting_row = math.ceil(starting_row)
                    if starting_col % 1 == 0:
                        starting_col -= 1
                    else:
                        starting_col = math.floor(starting_col)
                else:
                    starting_row = 0
                    starting_col = 0
                n_entity = 0
                for entity in self.embedding_entities:
                    ax = plt.subplot(gs[starting_row, starting_col])
                    if n_entity == 0:
                        ax.set_title("Indicator = {}".format(indicator))
                    if self.line_position[n_lines] != None:
                        ax.axvline(x=self.line_position[n_lines], color='r', linestyle='--', linewidth = 1)
                    n_lines += 1
                    row0_label = ax.twinx()
                    row0_label.tick_params(axis='both', labelsize=0, length = 0)
                    row0_label.set(ylabel="Variable = {}".format(entity))
                    n_entity += 1
                    starting_row += 1
                    sns.kdeplot(self.df[(self.df["Indicator"]==indicator) & (self.df["Variable"]==entity)]["Scores"],ax=ax)
        
            else:
                starting_row = 0
                starting_col = n_indic
                if indicator == "wang":
                    for time,reu in zip(self.time_window_cooc, self.n_reutilisation):
                        starting_row = 0
                        for variable in self.variables:
                            ax = plt.subplot(gs[starting_row, starting_col])
                            if starting_col != 0:
                                ax.set_ylabel(" ")
                            if starting_row != (grid_spec_row-1):
                                ax.set_xlabel(" ")
                            if starting_row == 0:
                                ax.set_title("Indicator = {}".format(indicator +"_{}_{}".format(time,reu)))
                            if starting_col == grid_spec_col-1:
                                row0_label = ax.twinx()
                                row0_label.tick_params(axis='both', labelsize=0, length = 0)
                                row0_label.set(ylabel="Variable = {}".format(variable))
                            if self.line_position[n_lines] != None:
                                ax.axvline(x=self.line_position[n_lines], color='r', linestyle='--', linewidth = 1)
                            n_lines += 1
                            starting_row += 1
                            sns.kdeplot(data = self.df[(self.df["Indicator"]== indicator +"_{}_{}".format(time,reu)) & (self.df["Variable"]==variable)]["Scores"],ax=ax)
                        n_indic += 1
                else:
                    for variable in self.variables:
                        ax = plt.subplot(gs[starting_row, starting_col])
                        if starting_col != 0:
                            ax.set_ylabel(" ")
                        if starting_row != (grid_spec_row-1):
                            ax.set_xlabel(" ")   
                        if starting_row == 0:
                            ax.set_title("Indicator = {}".format(indicator))
                        if starting_col == grid_spec_col-1:
                            row0_label = ax.twinx()
                            row0_label.tick_params(axis='both', labelsize=0, length = 0)
                            row0_label.set(ylabel="Variable = {}".format(variable))
                        if self.line_position[n_lines] != None:
                            ax.axvline(x=self.line_position[n_lines], color='r', linestyle='--', linewidth = 1)
                        n_lines += 1
                        starting_row += 1
                        sns.kdeplot(data = self.df[(self.df["Indicator"]==indicator) & (self.df["Variable"]==variable)]["Scores"],ax=ax)       
                    if indicator != "wang":
                        n_indic += 1
        plt.legend(handles=[plt.Line2D([], [], color="red", linestyle="--", linewidth = 1, label="Novelty score")])

class novelty_trend:

    def __init__(self,
                 year_range,
                 indicators,
                 id_variable,
                 variables = [],
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
        self.id_variable = id_variable
        self.variables = variables
        self.indicators = indicators
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        self.embedding_entities = embedding_entities
        self.shibayama_per =  shibayama_per
        
        if not isinstance(indicators, list):
            raise ValueError('indicators should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list for Wang et al')
        if "shibayama" in self.indicators:
            if not isinstance(embedding_entities, list):
                raise ValueError('embedding_entities should be a list for Shibayama et al.')
        else:
            if not isinstance(variables, list):
                raise ValueError('variables should be a list')
                
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
            if indicator =="shibayama":
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
            elif self.variables:
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
                                df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [variable, indicator + "_" + str(time) + "_" + str(reu), year]
                                self.df = pd.concat([self.df,df_temp], ignore_index=True)        
                    else:
                        key_name = variable + "_" + indicator
                        df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [variable, indicator]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    
    def get_info_json(self):
        for indicator in self.indicators:
            if indicator =="shibayama":
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
                            except Exception as e:
                                pass
                        df_temp = pd.DataFrame([np.mean(np.ma.masked_invalid(score_list))], columns=["Score_mean"])
                        df_temp['Variable'], df_temp['Indicator'], df_temp["Year"] = [embedding_entity, indicator, year]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)   
            elif self.variables:
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
                                df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [variable, indicator + "_" + str(time) + "_" + str(reu), year]
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
    
        if "shibayama" in self.indicators and len(self.indicators) > 2:
            grid_spec_col = len(self.indicators) - 1
        grid_spec_row = len(set(self.df["Variable"]))
        fig = plt.figure(figsize=(24, 16))
        gs = gridspec.GridSpec(grid_spec_row, grid_spec_col)
        
        
        n_indic = 0
        for indicator in self.indicators:
            if indicator == "shibayama":
                if len(self.indicators) > 1:
                    starting_row = int(grid_spec_row/2)
                    starting_col = int(grid_spec_col/2)
                    if starting_row % 1 != 0:
                        starting_row = math.ceil(starting_row)
                    if starting_col % 1 == 0:
                        starting_col -= 1
                    else:
                        starting_col = math.floor(starting_col)
                else:
                    starting_row = 0
                    starting_col = 0
                n_entity = 0
                for entity in self.embedding_entities:
                    ax = plt.subplot(gs[starting_row, starting_col])
                    if n_entity == 0:
                        ax.set_title("Indicator = {}".format(indicator))
                    row0_label = ax.twinx()
                    row0_label.tick_params(axis='both', labelsize=0, length = 0)
                    row0_label.set(ylabel="Variable = {}".format(entity))
                    n_entity += 1
                    starting_row += 1
                    sns.lineplot(data = self.df[(self.df["Indicator"]==indicator) & (self.df["Variable"]==entity)], x = "Year", y = "Score_mean",ax=ax)
        
            else:
                starting_row = 0
                starting_col = n_indic
                if indicator == "wang":
                    for time,reu in zip(self.time_window_cooc, self.n_reutilisation):
                        starting_row = 0
                        for variable in self.variables:
                            ax = plt.subplot(gs[starting_row, starting_col])
                            if starting_col != 0:
                                ax.set_ylabel(" ")
                            if starting_row != (grid_spec_row-1):
                                ax.set_xlabel(" ")
                            if starting_row == 0:
                                ax.set_title("Indicator = {}".format(indicator +"_{}_{}".format(time,reu)))
                            if starting_col == grid_spec_col-1:
                                row0_label = ax.twinx()
                                row0_label.tick_params(axis='both', labelsize=0, length = 0)
                                row0_label.set(ylabel="Variable = {}".format(variable))
                            starting_row += 1
                            sns.lineplot(data = self.df[(self.df["Indicator"]== indicator +"_{}_{}".format(time,reu)) & (self.df["Variable"]==variable)], x = "Year", y = "Score_mean",ax=ax)
                        n_indic += 1
                else:
                    for variable in self.variables:
                        ax = plt.subplot(gs[starting_row, starting_col])
                        if starting_col != 0:
                            ax.set_ylabel(" ")
                        if starting_row != (grid_spec_row-1):
                            ax.set_xlabel(" ")   
                        if starting_row == 0:
                            ax.set_title("Indicator = {}".format(indicator))
                        if starting_col == grid_spec_col-1:
                            row0_label = ax.twinx()
                            row0_label.tick_params(axis='both', labelsize=0, length = 0)
                            row0_label.set(ylabel="Variable = {}".format(variable))
                        starting_row += 1
                        sns.lineplot(data = self.df[(self.df["Indicator"]==indicator) & (self.df["Variable"]==variable)], x = "Year", y = "Score_mean",ax=ax)       
                if indicator != "wang":
                    n_indic += 1
        


class correlation_indicators:
    
    def __init__(self,
                 year_range,
                 indicators,
                 variables = [],
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
        
        if not isinstance(indicators, list):
            raise ValueError('indicators should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list for Wang et al')
        if "shibayama" in self.indicators:
            if not isinstance(embedding_entities, list):
                raise ValueError('embedding_entities should be a list for Shibayama et al.')
        else:
            if not isinstance(variables, list):
                raise ValueError('variables should be a list')
                
        self.corr = defaultdict(dict)
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()
    
    def get_info_mongo(self):
        pass
    
    def get_info_json(self):
        for indicator in self.indicators:
            if indicator =="shibayama":
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
            elif self.variables:
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
                sns.heatmap(cleaned_corr.corr(), cmap="Blues")
        else:
            cleaned_corr = pd.DataFrame()
            for year in self.year_range:
                cleaned_corr = pd.concat([cleaned_corr, self.corr[year][~self.corr[year].isin([np.nan, np.inf, -np.inf]).any(1)]], ignore_index=True)
            sns.heatmap(cleaned_corr.corr(), cmap="Blues")
                        
