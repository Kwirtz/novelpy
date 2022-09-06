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
                 keep_item_percentile = None,
                 embedding_entities_shibayama = None,
                 shibayma_per = 10,
                 embedding_entities_authors = None,
                 authors_per = 10,
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
        self.embedding_entities_shibayama = embedding_entities_shibayama
        self.shibayma_per = shibayma_per
        self.embedding_entities_authors = embedding_entities_authors
        self.authors_per = authors_per
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        self.keep_item_percentile = keep_item_percentile
        
        if not isinstance(indicators, list):
            raise ValueError('indicators should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list) or not isinstance(keep_item_percentile, list):
                raise ValueError('time_window_cooc, n_reutilisation and keep_item_percentile should be a list for Wang et al')
        if "shibayama" in self.indicators:
            if not isinstance(embedding_entities_shibayama, list):
                raise ValueError('embedding_entities should be a list for Shibayama et al.')
        if "Author_proximity" in self.indicators:
            if not isinstance(embedding_entities_authors, list):
                raise ValueError('embedding_entities should be a list for Pelletier and Wirtz (2021).')
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

        
        self.line_position = []
        for indicator in self.indicators:
            if indicator =="shibayama":
                key_name = "shibayama"
                collection = self.db["output_shibayama"]
                for embedding_entity in self.embedding_entities_shibayama:
                    doc = collection.find_one({self.id_variable:self.doc_id,
                                               "year":self.doc_year,
                                               "scores_array_{}_embedding".format(embedding_entity):{"$exists":1} })
                    df_temp = pd.DataFrame(doc["scores_array_{}_embedding".format(embedding_entity)], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [embedding_entity, indicator]   
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    self.line_position.append(float(np.percentile(a = doc["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayma_per)))
            elif indicator == "Author_proximity":
                key_name = "Author_proximity"
                collection_author = self.db["output_authors"]
                for embedding_entity in self.embedding_entities_authors:
                    
                    # intra
                    doc_author = collection_author.find({"PMID":self.doc["PMID"],"type":"intra"})
                    scores_array = []
                    for doc in doc_author:
                        scores_array += doc["score_array_authors_novelty_{}_5".format(embedding_entity)]["score_array"]
                    df_temp_intra = pd.DataFrame(scores_array, columns=["Scores"])
                    df_temp_intra['Variable'], df_temp_intra['Indicator'] = [embedding_entity, indicator + "_intra"]
                    
                    # inter
                    doc_author = collection_author.find({"PMID":self.doc["PMID"],"type":"inter"})
                    scores_array = []
                    for doc in doc_author:
                        scores_array += doc["score_array_authors_novelty_{}_5".format(embedding_entity)]["score_array"]
                    df_temp_inter = pd.DataFrame(doc_author["score_array"]["inter"], columns=["Scores"])
                    df_temp_inter['Variable'], df_temp_inter['Indicator'] = [embedding_entity, indicator+ "_inter"] 
                    
                    self.df = pd.concat([self.df,df_temp_intra,df_temp_inter], ignore_index=True)
                    self.line_position.append(float(np.percentile(a = doc_author["score_array"]["intra"],
                                                                  q = self.authors_per)))
                    self.line_position.append(float(np.percentile(a = doc_author["score_array"]["inter"],
                                                                  q = self.authors_per)))                    
            elif self.variables:
                for variable in self.variables:
                    if indicator == 'wang':
                        for time, reu, perc in zip(self.time_window_cooc,self.n_reutilisation, self.keep_item_percentile):
                            collection = self.db["output_wang_{}_{}_{}_restricted{}".format(variable,str(time),str(reu),str(perc))]
                            key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu) + "_restricted" + str(perc)
                            doc = collection.find_one({self.id_variable:self.doc_id,
                                                       "year":self.doc_year})
                            df_temp = pd.DataFrame(doc[key_name]["scores_array"], columns=["Scores"])
                            df_temp['Variable'], df_temp['Indicator'] = [variable, indicator + "_" + str(time) + "_" + str(reu)+ "_restricted" + str(perc)]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)
                            self.line_position.append(doc[key_name]["score"]["novelty"])
                    else:
                        collection = self.db["output_{}_{}".format(indicator,variable)]
                        doc = collection.find_one({self.id_variable:self.doc_id,
                                                   "year":self.doc_year})
                        key_name = variable + "_" + indicator
                        df_temp = pd.DataFrame(doc[key_name]["scores_array"], columns=["Scores"])
                        df_temp['Variable'], df_temp['Indicator'] = [variable, indicator]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)
                        self.line_position.append(doc[key_name]["score"]["novelty"])

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
                    raise Exception("No object with the ID {} or not enough combinations to have a score on entity {} and indicator {}".format(self.doc_id, self.embedding_entities_shibayama[0],indicator))
                for embedding_entity in self.embedding_entities_shibayama:
                    df_temp = pd.DataFrame(self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"], columns=["Scores"])
                    df_temp['Variable'], df_temp['Indicator'] = [embedding_entity, indicator]   
                    self.df = pd.concat([self.df,df_temp], ignore_index=True)
                    self.line_position.append(float(np.percentile(a = self.doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayma_per)))    
            elif indicator == "Author_proximity":
                key_name = "Author_proximity"   
                self.path_doc= "Result/{}/{}".format(indicator,self.doc_year)
                with open(self.path_doc + ".json", "r") as read_file:
                    self.docs = json.load(read_file)
                try:
                    self.doc = [x for x in self.docs if x[self.id_variable] == self.doc_id][0]                    
                except:
                    raise Exception("No object with the ID {} or not enough combinations to have a score on entity {} and indicator {}".format(self.doc_id, self.embedding_entities_shibayama[0],indicator))
                for embedding_entity in self.embedding_entities_authors:
                    df_temp_intra = pd.DataFrame(self.doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_intra"], columns=["Scores"])
                    df_temp_inter = pd.DataFrame(self.doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_inter"], columns=["Scores"])
                    df_temp_intra['Variable'], df_temp_intra['Indicator'] = [embedding_entity, indicator + "_intra"]   
                    df_temp_inter['Variable'], df_temp_inter['Indicator'] = [embedding_entity, indicator+ "_inter"] 
                    self.df = pd.concat([self.df,df_temp_intra,df_temp_inter], ignore_index=True)
                    self.line_position.append(float(np.percentile(a = self.doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_intra"],
                                                                  q = self.authors_per)))
                    self.line_position.append(float(np.percentile(a = self.doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_inter"],
                                                                  q = self.authors_per)))        
            elif self.variables:
                for variable in self.variables:
                    if indicator == 'wang':
                        for time, reu, perc in zip(self.time_window_cooc,self.n_reutilisation, self.keep_item_percentile):
                            key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu) + "_restricted" + str(perc)
                            self.path_doc= "Result/{}/{}/{}".format(indicator, variable + "_" + str(time) + "_" + str(reu)  + "_restricted" + str(perc) ,self.doc_year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                self.docs = json.load(read_file)
                            try:
                                self.doc = [doc for doc in self.docs if doc[self.id_variable] == self.doc_id][0]
                            except:
                                raise Exception("No object with the ID {} or not enough combinations to have a score on entity {} and indicator {}".format(self.doc_id,variable,indicator))
                            self.line_position.append(self.doc[key_name]["score"]["novelty"])
                            df_temp = pd.DataFrame(self.doc[key_name]["scores_array"], columns=["Scores"])
                            df_temp['Variable'], df_temp['Indicator'] = [variable, indicator + "_" + str(time) + "_" + str(reu) + "_restricted" + str(perc)]
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
        if "shibayama" in self.indicators and "Author_proximity" in self.indicators and len(self.indicators) > 3:
            grid_spec_col = len(self.indicators) - 2
        elif "shibayama" in self.indicators and len(self.indicators) > 2 or "Author_proximity" in self.indicators and len(self.indicators) > 2:
            grid_spec_col = len(self.indicators) - 1
        else:
            grid_spec_col = len(self.indicators)
        grid_spec_row = len(set(self.df["Variable"]))
        
        fig = plt.figure(figsize=(24, 16))
        fig.suptitle('doc ID:{}'.format(self.doc_id), fontsize=16)
        gs = gridspec.GridSpec(grid_spec_row, grid_spec_col)
        n_indic = 0
        n_lines = 0
        for indicator in self.indicators:
            if indicator == "shibayama":
                if len(self.indicators) > 1 and "Author_proximity" not in self.indicators:
                    starting_row = int(grid_spec_row/2)
                    starting_col = int(grid_spec_col/2)
                    if starting_row % 2 != 0:
                        starting_row = math.ceil(starting_row)
                    if starting_col % 2 == 0:
                        starting_col -= 1
                    else:
                        starting_col = math.floor(starting_col)
                elif len(self.indicators) > 2 and "shibayama" in self.indicators and "Author_proximity" in self.indicators:
                    starting_row = int(grid_spec_row/2)
                    starting_col = int(grid_spec_col/2)
                    if starting_row % 2 != 0:
                        starting_row = math.ceil(starting_row)
                    starting_col = math.ceil(starting_col)-1
                elif len(self.indicators) == 2 and "shibayama" in self.indicators and "Author_proximity" in self.indicators:
                    starting_row = 0
                    starting_col = 0
                else:
                    starting_row = 0
                    starting_col = 0
                n_entity = 0
                for entity in self.embedding_entities_shibayama:
                    ax = plt.subplot(gs[starting_row, starting_col])
                    if n_entity == 0:
                        ax.set_title("Indicator = {}".format(indicator))
                    if self.line_position[n_lines] != None:
                        ax.axvline(x=self.line_position[n_lines], color='r', linestyle='--', linewidth = 1)
                    n_lines += 1
                    if "Author_proximity" in self.indicators:
                        row0_label = ax.twinx()
                        row0_label.tick_params(axis='both', labelsize=0, length = 0)
                        row0_label.set(ylabel=" ")
                    else:
                        row0_label = ax.twinx()
                        row0_label.tick_params(axis='both', labelsize=0, length = 0)
                        row0_label.set(ylabel="Variable = {}".format(entity))
                    n_entity += 1
                    starting_row += 1
                    sns.kdeplot(self.df[(self.df["Indicator"]==indicator) & (self.df["Variable"]==entity)]["Scores"],ax=ax)
            elif indicator == "Author_proximity":
                if len(self.indicators) > 2:
                    starting_row = int(grid_spec_row/2)
                    starting_col = int(grid_spec_col/2)
                    if starting_row % 2 != 0:
                        starting_row = math.ceil(starting_row)
                    if starting_col % 2 != 0:
                        starting_col = math.ceil(starting_col)
                elif len(self.indicators) == 2 and "shibayama" in self.indicators and "Author_proximity" in self.indicators:
                    starting_row = 0
                    starting_col = 1
                else:
                    starting_row = 0
                    starting_col = 0
                n_entity = 0
                for entity in self.embedding_entities_authors:
                    ax = plt.subplot(gs[starting_row, starting_col])
                    if "shibayama" in self.indicators:
                        ax.set_ylabel(" ")
                    if n_entity == 0:
                        ax.set_title("Indicator = {}".format(indicator))
                    for i in range(2):
                        if self.line_position[n_lines] != None:
                            ax.axvline(x=self.line_position[n_lines], color='r', linestyle='--', linewidth = 1)
                        n_lines += 1
                    row0_label = ax.twinx()
                    row0_label.tick_params(axis='both', labelsize=0, length = 0)
                    row0_label.set(ylabel="Variable = {}".format(entity))
                    df1 = self.df[(self.df["Indicator"]=="Author_proximity_inter") | (self.df["Indicator"]=="Author_proximity_intra") & (self.df["Variable"]==entity)]["Scores"]
                    df2 = self.df[(self.df["Indicator"]=="Author_proximity_inter") | (self.df["Indicator"]=="Author_proximity_intra") & (self.df["Variable"]==entity)]["Indicator"]
                    df3 = pd.concat([df1, df2], axis=1) 
                    palette = {"Author_proximity_intra":"gray", "Author_proximity_inter":"tab:orange"}
                    if n_entity == 0:
                        sns.kdeplot(data = df3, x = "Scores", hue = "Indicator",ax=ax, palette = palette, legend = False)   
                    else:
                        sns.kdeplot(data = df3, x = "Scores", hue = "Indicator",ax=ax, palette = palette)  
                    print(starting_row,starting_col)
                    n_entity += 1
                    starting_row += 1
            else:
                starting_row = 0
                starting_col = n_indic
                if indicator == "wang":
                    for time, reu, perc in zip(self.time_window_cooc, self.n_reutilisation, self.keep_item_percentile):
                        starting_row = 0
                        for variable in self.variables:
                            ax = plt.subplot(gs[starting_row, starting_col])
                            if starting_col != 0:
                                ax.set_ylabel(" ")
                            if starting_row != (grid_spec_row-1):
                                ax.set_xlabel(" ")
                            if starting_row == 0:
                                ax.set_title("Indicator = {}".format(indicator +"_{}_{}_restricted{}".format(time,reu,perc)))
                            if starting_col == grid_spec_col-1:
                                row0_label = ax.twinx()
                                row0_label.tick_params(axis='both', labelsize=0, length = 0)
                                row0_label.set(ylabel="Variable = {}".format(variable))
                            if self.line_position[n_lines] != None:
                                ax.axvline(x=self.line_position[n_lines], color='r', linestyle='--', linewidth = 1)
                            n_lines += 1
                            starting_row += 1
                            sns.kdeplot(data = self.df[(self.df["Indicator"]== indicator +"_{}_{}_restricted{}".format(time,reu,perc)) & (self.df["Variable"]==variable)]["Scores"],ax=ax)
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
        plt.legend(handles=[plt.Line2D([], [], color="red", linestyle="--", linewidth = 1, label="Novelty score")],loc="lower left",bbox_to_anchor=(1.05, 1.0))

class novelty_trend:

    def __init__(self,
                 year_range,
                 indicators,
                 id_variable,
                 variables = [],
                 time_window_cooc = None,
                 n_reutilisation = None,
                 keep_item_percentile = None,
                 embedding_entities_shibayama = None,
                 shibayama_per = 10,
                 embedding_entities_authors = None,
                 authors_per = 10,
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
        self.keep_item_percentile = keep_item_percentile
        self.embedding_entities_shibayama = embedding_entities_shibayama
        self.shibayama_per =  shibayama_per
        self.embedding_entities_authors = embedding_entities_authors
        self.authors_per = authors_per
        
        if not isinstance(indicators, list):
            raise ValueError('indicators should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list for Wang et al')
        if "shibayama" in self.indicators:
            if not isinstance(embedding_entities_shibayama, list):
                raise ValueError('embedding_entities_shibayama should be a list for Shibayama et al.')
        if "Authors_proximity" in self.indicators:
            if not isinstance(embedding_entities_authors, list):
                raise ValueError('embedding_entities should be a list for Pelletier and Wirtz (2021).')
        else:
            if not isinstance(variables, list):
                raise ValueError('variables should be a list')
                
        self.df = pd.DataFrame(columns = ["Score_mean","Variable","Indicator","Year"])
        self.trend = defaultdict(dict)
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()
    

    def get_info_mongo(self):                
        self.client = pymongo.MongoClient(self.client_name)
        self.db = self.client[self.db_name]
        
        
        
        for indicator in self.indicators:
            print(indicator)
            if indicator =="shibayama":
                for embedding_entity in self.embedding_entities_shibayama:
                    for year in self.year_range:
                            collection = self.db["output_shibayama"]
                            docs = collection.find({"year":year,
                                                    "scores_array_{}_embedding".format(embedding_entity):{"$exists":1}})
                            score_list = []
                            for doc in docs:
                                try:
                                    score_list.append(float(np.percentile(a = doc["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayama_per)))
                                except:
                                    continue
                            df_temp = pd.DataFrame([np.mean(score_list)], columns=["Score_mean"])
                            df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [embedding_entity, indicator, year]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)       


                            
            elif indicator =="Author_proximity":
                key_name = "Author_proximity"
                for embedding_entity in self.embedding_entities_authors:
                    collection_author = self.db["output_authors"]
                    for year in self.year_range:
                            docs = collection_author.find({"year":year})
                            score_list_intra = []
                            score_list_inter = []
                            for doc in docs:
                                try:
                                    score_list_intra.append(float(np.percentile(a = doc["score_array"]["intra"],
                                                                  q = self.authors_per)))
                                except:
                                    continue
                                try:
                                    score_list_inter.append(float(np.percentile(a = doc["score_array"]["inter"],
                                                                  q = self.authors_per)))
                                except:
                                    continue
                            df_temp_intra = pd.DataFrame([np.mean(score_list_intra)], columns=["Score_mean"])
                            df_temp_intra['Variable'], df_temp_intra['Indicator'], df_temp_intra['Year'] = [embedding_entity, indicator + "_intra", year]
                            df_temp_inter = pd.DataFrame([np.mean(score_list_inter)], columns=["Score_mean"])
                            df_temp_inter['Variable'], df_temp_inter['Indicator'], df_temp_inter['Year'] = [embedding_entity, indicator + "_inter", year] 
                            self.df = pd.concat([self.df,df_temp_intra,df_temp_inter], ignore_index=True)         
            
            elif self.variables:
                for variable in self.variables:
                    if indicator == 'wang':
                        for time,reu,perc in zip(self.time_window_cooc,self.n_reutilisation,self.keep_item_percentile):
                            key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu) + "_restricted" + str(perc)
                            collection = self.db["output_wang_{}_{}_{}_restricted{}".format(variable,time,reu,perc)]
                            for year in self.year_range:
                                docs = collection.find({"year":year})
                                score_list = []
                                for doc in docs:
                                    try:
                                        score_list.append(doc[key_name]["score"]["novelty"])   
                                    except:
                                        continue
                                df_temp = pd.DataFrame([np.mean(score_list)], columns=["Score_mean"])
                                df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [variable, indicator + "_" + str(time) + "_" + str(reu)+ "_restricted" + str(perc), year]
                                self.df = pd.concat([self.df,df_temp], ignore_index=True)        
                    else:
                        key_name = variable + "_" + indicator
                        collection = self.db["output_{}_{}".format(indicator,variable)]
                        for year in self.year_range:
                            docs = collection.find({"year":year})
                            score_list = []
                            for doc in docs:
                                try:
                                    score_list.append(doc[key_name]["score"]["novelty"])   
                                except:
                                    continue
                            df_temp = pd.DataFrame([np.mean(np.ma.masked_invalid(score_list))], columns=["Score_mean"])
                            df_temp['Variable'], df_temp['Indicator'], df_temp["Year"] = [variable, indicator, year]
                            self.df = pd.concat([self.df,df_temp], ignore_index=True)    




        """
        for year in self.year_range:
            docs = self.collection.find({"year":year})
            for doc in tqdm.tqdm(docs):
                for indicator in self.indicators:
                    if indicator =="shibayama":
                        key_name = "shibayama"   
                        for embedding_entity in self.embedding_entities_shibayama:
                            try:
                                to_append = float(np.percentile(a = doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayama_per))
                            except:
                                continue     
                            try:
                                self.trend[year][key_name + "_" + embedding_entity] += [to_append]
                            except:
                                self.trend[year][key_name + "_" + embedding_entity] = []
                    elif indicator =="Author_proximity":
                        key_name = "Author_proximity"   
                        for embedding_entity in self.embedding_entities_authors:
                            try:
                                to_append_intra = float(np.percentile(a = doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_intra"],
                                                                  q = self.authors_per))
                            except:
                                to_append_intra = None
                            try:
                                to_append_inter = float(np.percentile(a = doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_inter"],
                                                                  q = self.authors_per))
                            except:
                                to_append_inter = None
                            if to_append_intra:
                                try:
                                    self.trend[year][key_name + "_" + embedding_entity + "_5_intra"] += [to_append_intra]
                                except:
                                    self.trend[year][key_name + "_" + embedding_entity + "_5_intra"] = []
                            if to_append_inter:
                                try:
                                    self.trend[year][key_name + "_" + embedding_entity + "_5_inter"] += [to_append_inter]
                                except:
                                    self.trend[year][key_name + "_" + embedding_entity + "_5_inter"] = []
                    elif indicator == "disruptiveness":
                        key_name = "disruptiveness"
                        for measure in self.disruptiveness_measures:
                            try:
                                to_append = doc[key_name][measure]
                            except:
                                continue
                            try:
                                self.trend[year][key_name + "_" + measure] += [to_append]
                            except:
                                self.trend[year][key_name + "_" + measure] = []
                    elif self.variables:
                        for variable in self.variables:
                            if indicator == 'wang':
                                for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                                    key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                                    try:
                                       to_append = doc[key_name]["score"]["novelty"]
                                    except:
                                        continue
                                    try:
                                        self.trend[year][key_name] += [to_append]
                                    except:
                                        self.trend[year][key_name] = []
                            else:
                                key_name = variable + "_" + indicator
                                try:
                                   to_append = doc[key_name]["score"]["novelty"]
                                except:
                                    continue
                                try:
                                    self.trend[year][key_name] += [to_append]
                                except:
                                    self.trend[year][key_name] = [] 
        """
        for year in self.year_range:
            self.trend[year] = pd.DataFrame.from_dict(self.trend[year], orient='index').T     

    
                    
    def get_info_json(self):
        for indicator in self.indicators:
            if indicator =="shibayama":
                key_name = "shibayama"
                for embedding_entity in self.embedding_entities_shibayama:
                    for year in self.year_range:
                        self.path_doc= "Result/{}/{}".format(indicator, year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            docs = json.load(read_file)   
                        score_list = []
                        for doc in docs:
                            try:
                                score_list.append(float(np.percentile(a = doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayama_per)))
                            except Exception as e:
                                pass
                        df_temp = pd.DataFrame([np.mean(np.ma.masked_invalid(score_list))], columns=["Score_mean"])
                        df_temp['Variable'], df_temp['Indicator'], df_temp["Year"] = [embedding_entity, indicator, year]
                        self.df = pd.concat([self.df,df_temp], ignore_index=True)   
            elif indicator =="Author_proximity":
                key_name = "Author_proximity"
                for embedding_entity in self.embedding_entities_authors:
                    for year in self.year_range:
                            self.path_doc= "Result/{}/{}".format(indicator, year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                docs = json.load(read_file)   
                            score_list_intra = []
                            score_list_inter = []
                            for doc in docs:
                                try:
                                    score_list_intra.append(float(np.percentile(a = doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_intra"],
                                                                  q = self.authors_per)))
                                except:
                                    continue
                                try:
                                    score_list_inter.append(float(np.percentile(a = doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_inter"],
                                                                  q = self.authors_per)))
                                except:
                                    continue
                            df_temp_intra = pd.DataFrame([np.mean(score_list_intra)], columns=["Score_mean"])
                            df_temp_intra['Variable'], df_temp_intra['Indicator'], df_temp_intra['Year'] = [embedding_entity, indicator + "_intra", year]
                            df_temp_inter = pd.DataFrame([np.mean(score_list_inter)], columns=["Score_mean"])
                            df_temp_inter['Variable'], df_temp_inter['Indicator'], df_temp_inter['Year'] = [embedding_entity, indicator + "_inter", year] 
                            self.df = pd.concat([self.df,df_temp_intra,df_temp_inter], ignore_index=True)                     
            elif self.variables:
                for variable in self.variables:
                    if indicator == 'wang':
                        for time,reu,perc in zip(self.time_window_cooc,self.n_reutilisation,self.keep_item_percentile):
                            key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                            for year in self.year_range:
                                self.path_doc= "Result/{}/{}/{}".format(indicator, variable + "_" + str(time) + "_" + str(reu)+ "_restricted" + str(perc) , year)
                                with open(self.path_doc + ".json", "r") as read_file:
                                    docs = json.load(read_file)
                                score_list = []
                                for doc in docs:
                                    try:
                                        score_list.append(doc[key_name]["score"]["novelty"])
                                    except:
                                        continue
                                df_temp = pd.DataFrame([np.mean(score_list)], columns=["Score_mean"])
                                df_temp['Variable'], df_temp['Indicator'], df_temp['Year'] = [variable, indicator + "_" + str(time) + "_" + str(reu)+ "_restricted" + str(perc), year]
                                self.df = pd.concat([self.df,df_temp], ignore_index=True)                           
    
                    else:                        
                        key_name = variable + "_" + indicator
                        for year in self.year_range:
                            self.path_doc= "Result/{}/{}/{}".format(indicator, variable, year)
                            with open(self.path_doc + ".json", "r") as read_file:
                                docs = json.load(read_file)
                            score_list = []
                            for doc in docs:
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
    
        if "shibayama" in self.indicators and "Author_proximity" in self.indicators and len(self.indicators) > 3:
            grid_spec_col = len(self.indicators) - 2
        elif "shibayama" in self.indicators and len(self.indicators) > 2 or "Author_proximity" in self.indicators and len(self.indicators) > 2:
            grid_spec_col = len(self.indicators) - 1
        else:
            grid_spec_col = len(self.indicators)
        grid_spec_row = len(set(self.df["Variable"]))
        
        fig = plt.figure(figsize=(24, 16))
        gs = gridspec.GridSpec(grid_spec_row, grid_spec_col)
        
        
        n_indic = 0
        for indicator in self.indicators:
            if indicator == "shibayama":
                if len(self.indicators) > 1 and "Author_proximity" not in self.indicators:
                    starting_row = int(grid_spec_row/2)
                    starting_col = int(grid_spec_col/2)
                    if starting_row % 2 != 0:
                        starting_row = math.ceil(starting_row)
                    if starting_col % 2 == 0:
                        starting_col -= 1
                    else:
                        starting_col = math.floor(starting_col)
                elif len(self.indicators) > 2 and "shibayama" in self.indicators and "Author_proximity" in self.indicators:
                    starting_row = int(grid_spec_row/2)
                    starting_col = int(grid_spec_col/2)
                    if starting_row % 2 != 0:
                        starting_row = math.ceil(starting_row)
                    starting_col = math.ceil(starting_col)-1
                elif len(self.indicators) == 2 and "shibayama" in self.indicators and "Author_proximity" in self.indicators:
                    starting_row = 0
                    starting_col = 0
                else:
                    starting_row = 0
                    starting_col = 0
                n_entity = 0
                for entity in self.embedding_entities_shibayama:
                    ax = plt.subplot(gs[starting_row, starting_col])
                    if n_entity == 0:
                        ax.set_title("Indicator = {}".format(indicator))
                    row0_label = ax.twinx()
                    row0_label.tick_params(axis='both', labelsize=0, length = 0)
                    row0_label.set(ylabel="Variable = {}".format(entity))
                    n_entity += 1
                    starting_row += 1
                    sns.lineplot(data = self.df[(self.df["Indicator"]==indicator) & (self.df["Variable"]==entity)], x = "Year", y = "Score_mean",ax=ax)
            elif indicator == "Author_proximity":
                if len(self.indicators) > 2:
                    starting_row = int(grid_spec_row/2)
                    starting_col = int(grid_spec_col/2)
                    if starting_row % 2 != 0:
                        starting_row = math.ceil(starting_row)
                    if starting_col % 2 != 0:
                        starting_col = math.ceil(starting_col)
                elif len(self.indicators) == 2 and "shibayama" in self.indicators and "Author_proximity" in self.indicators:
                    starting_row = 0
                    starting_col = 1
                else:
                    starting_row = 0
                    starting_col = 0
                n_entity = 0
                for entity in self.embedding_entities_authors:
                    ax = plt.subplot(gs[starting_row, starting_col])
                    if "shibayama" in self.indicators:
                        ax.set_ylabel(" ")
                    if n_entity == 0:
                        ax.set_title("Indicator = {}".format(indicator))
                    row0_label = ax.twinx()
                    row0_label.tick_params(axis='both', labelsize=0, length = 0)
                    row0_label.set(ylabel="Variable = {}".format(entity))
                    df1 = self.df[(self.df["Indicator"]=="Author_proximity_inter") | (self.df["Indicator"]=="Author_proximity_intra") & (self.df["Variable"]==entity)]["Score_mean"]
                    df2 = self.df[(self.df["Indicator"]=="Author_proximity_inter") | (self.df["Indicator"]=="Author_proximity_intra") & (self.df["Variable"]==entity)]["Indicator"]
                    df3 = self.df[(self.df["Indicator"]=="Author_proximity_inter") | (self.df["Indicator"]=="Author_proximity_intra") & (self.df["Variable"]==entity)]["Year"]
                    df4 = pd.concat([df1, df2, df3], axis=1) 
                    palette = {"Author_proximity_intra":"gray", "Author_proximity_inter":"tab:orange"}
                    if n_entity == 0:
                        sns.lineplot(data = df4, x = "Year", y = "Score_mean", hue = "Indicator",ax=ax, palette = palette, legend = False,ci=None)
                    else:
                        sns.lineplot(data = df4, x = "Year", y = "Score_mean", hue = "Indicator",ax=ax, palette = palette,ci=None)
                    n_entity += 1
                    starting_row += 1        
            else:
                starting_row = 0
                starting_col = n_indic
                if indicator == "wang":
                    for time,reu,perc in zip(self.time_window_cooc, self.n_reutilisation,self.keep_item_percentile):
                        starting_row = 0
                        for variable in self.variables:
                            ax = plt.subplot(gs[starting_row, starting_col])
                            if starting_col != 0:
                                ax.set_ylabel(" ")
                            if starting_row != (grid_spec_row-1):
                                ax.set_xlabel(" ")
                            if starting_row == 0:
                                ax.set_title("Indicator = {}".format(indicator +"_{}_{}_restricted{}".format(time,reu,perc)))
                            if starting_col == grid_spec_col-1:
                                row0_label = ax.twinx()
                                row0_label.tick_params(axis='both', labelsize=0, length = 0)
                                row0_label.set(ylabel="Variable = {}".format(variable))
                            starting_row += 1
                            sns.lineplot(data = self.df[(self.df["Indicator"]== indicator +"_{}_{}_restricted{}".format(time,reu,perc)) & (self.df["Variable"]==variable)], x = "Year", y = "Score_mean",ax=ax)
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
                 keep_item_percentile = 50,
                 embedding_entities_shibayama = None,
                 shibayama_per = 10,
                 embedding_entities_authors = None,
                 authors_per = 10,
                 disruptiveness_measures = None,
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
        self.keep_item_percentile = keep_item_percentile
        self.embedding_entities_shibayama = embedding_entities_shibayama
        self.shibayama_per = shibayama_per
        self.embedding_entities_authors = embedding_entities_authors        
        self.authors_per = authors_per
        self.disruptiveness_measures = disruptiveness_measures
        
        if not isinstance(indicators, list):
            raise ValueError('indicators should be a list')
        if "wang" in self.indicators:
            if not isinstance(time_window_cooc, list) or not isinstance(n_reutilisation, list):
                raise ValueError('time_window_cooc and n_reutilisation should be a list for Wang et al')
        if "disruptiveness" in self.indicators:
            if not isinstance(disruptiveness_measures, list):
                raise ValueError('disruptiveness_measures should be a list')            
        if "shibayama" in self.indicators:
            if not isinstance(embedding_entities_shibayama, list):
                raise ValueError('embedding_entities_shibayama should be a list for Shibayama et al.')
        else:
            if not isinstance(variables, list):
                raise ValueError('variables should be a list')
                
        self.corr = defaultdict(dict)
        if self.client_name:
            self.get_info_mongo()
        else:
            self.get_info_json()
    
    def get_info_mongo(self):
        
        self.client = pymongo.MongoClient(self.client_name)
        self.db = self.client[self.db_name]
        
        
        
        for indicator in self.indicators:
            print(indicator)
            if indicator =="shibayama":
                for embedding_entity in self.embedding_entities_shibayama:
                    for year in self.year_range:
                            collection = self.db["output_shibayama"]
                            docs = collection.find({"year":year,
                                                    "scores_array_{}_embedding".format(embedding_entity):{"$exists":1}})
                            for doc in docs:
                                try:
                                    to_append = float(np.percentile(a = doc["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayama_per))
                                except:
                                    continue
                                try:
                                    self.corr[year]["shibayama_" + embedding_entity] += [to_append]
                                except:
                                    self.corr[year]["shibayama_" +  embedding_entity] = []   

            elif indicator == "disruptiveness":
                key_name = "disruptiveness"
                collection = self.db["output_disruptiveness"]
                for measure in self.disruptiveness_measures:
                    for year in self.year_range:
                        docs = collection.find({"year":year})
                        for doc in docs:
                            try:
                                to_append = doc[key_name][measure]
                            except:
                                continue
                            try:
                                self.corr[year][key_name + "_" + measure] += [to_append]
                            except:
                                self.corr[year][key_name + "_" + measure] = []  
                                
            elif indicator =="Author_proximity":
                key_name = "Author_proximity"
                for embedding_entity in self.embedding_entities_authors:
                    collection_author = self.db["output_authors"]
                    for year in self.year_range:
                            docs = collection_author.find({"year":year})
                            for doc in docs:
                                try:
                                    score_list_intra.append(float(np.percentile(a = doc["score_array"]["intra"],
                                                                  q = self.authors_per)))
                                except:
                                    continue
                                try:
                                    score_list_inter.append(float(np.percentile(a = doc["score_array"]["inter"],
                                                                  q = self.authors_per)))
                                except:
                                    continue
            
            elif self.variables:
                for variable in self.variables:
                    if indicator == 'wang':
                        for time,reu,perc in zip(self.time_window_cooc,self.n_reutilisation,self.keep_item_percentile):
                            key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu) + "_restricted" + str(perc)
                            collection = self.db["output_wang_{}_{}_{}_restricted{}".format(variable,time,reu,perc)]
                            for year in self.year_range:
                                docs = collection.find({"year":year})
                                for doc in docs:
                                    try:
                                        to_append = doc[key_name]["score"]["novelty"]
                                    except:
                                        continue
                                    try:
                                        self.corr[year][key_name] += [to_append]
                                    except:
                                        self.corr[year][key_name] = []
                    else:
                        key_name = variable + "_" + indicator
                        collection = self.db["output_{}_{}".format(indicator,variable)]
                        for year in self.year_range:
                            docs = collection.find({"year":year})
                            for doc in docs:
                                try:
                                    to_append = doc[key_name]["score"]["novelty"]
                                except:
                                    continue
                                try:
                                    self.corr[year][key_name] += [to_append]
                                except:
                                    self.corr[year][key_name] = []
        """
        for year in self.year_range:
            docs = self.collection.find({"year":year})
            for doc in tqdm.tqdm(docs):
                for indicator in self.indicators:
                    if indicator =="shibayama":
                        key_name = "shibayama" 
                        collection = self.db["output"]
                        for embedding_entity in self.embedding_entities_shibayama:
                            try:
                                to_append = float(np.percentile(a = doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayama_per))
                            except:
                                continue     
                            try:
                                self.corr[year][key_name + "_" + embedding_entity] += [to_append]
                            except:
                                self.corr[year][key_name + "_" + embedding_entity] = []


                                
                    elif indicator =="Author_proximity":
                        key_name = "Author_proximity"
                        collection = self.db["output"]
                        for embedding_entity in self.embedding_entities_authors:
                            doc_author = collection.find_one({"PMID":doc["PMID"],"entity":embedding_entity})
                            try:
                                to_append_intra = float(np.percentile(a = doc_author["score_array"]["intra"],
                                                                  q = self.authors_per))
                            except:
                                to_append_intra = None
                            try:
                                to_append_inter = float(np.percentile(a = doc_author["score_array"]["inter"],
                                                                  q = self.authors_per))
                            except:
                                to_append_inter = None
                            if to_append_intra:
                                try:
                                    self.corr[year][key_name + "_" + embedding_entity + "_5_intra"] += [to_append_intra]
                                except:
                                    self.corr[year][key_name + "_" + embedding_entity + "_5_intra"] = []
                            if to_append_inter:
                                try:
                                    self.corr[year][key_name + "_" + embedding_entity + "_5_inter"] += [to_append_inter]
                                except:
                                    self.corr[year][key_name + "_" + embedding_entity + "_5_inter"] = []
                                    
                    elif indicator == "disruptiveness":
                        key_name = "disruptiveness"
                        for measure in self.disruptiveness_measures:
                            try:
                                to_append = doc[key_name][measure]
                            except:
                                continue
                            try:
                                self.corr[year][key_name + "_" + measure] += [to_append]
                            except:
                                self.corr[year][key_name + "_" + measure] = []
                                
                    elif self.variables:
                        for variable in self.variables:
                            if indicator == 'wang':
                                for time,reu in zip(self.time_window_cooc,self.n_reutilisation):
                                    key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu)
                                    try:
                                       to_append = doc[key_name]["score"]["novelty"]
                                    except:
                                        continue
                                    try:
                                        self.corr[year][key_name] += [to_append]
                                    except:
                                        self.corr[year][key_name] = []
                            else:
                                key_name = variable + "_" + indicator
                                try:
                                   to_append = doc[key_name]["score"]["novelty"]
                                except:
                                    continue
                                try:
                                    self.corr[year][key_name] += [to_append]
                                except:
                                    self.corr[year][key_name] = [] 

    """    
        for year in self.year_range:
            self.corr[year] = pd.DataFrame.from_dict(self.corr[year], orient='index').T                    

    
    def get_info_json(self):
        for indicator in self.indicators:
            if indicator =="shibayama":
                key_name = "shibayama"
                for embedding_entity in self.embedding_entities_shibayama:
                    for year in self.year_range:
                        self.path_doc= "Result/{}/{}".format(indicator, year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            docs = json.load(read_file)   
                        score_list = []
                        for doc in docs:
                            try:
                                score_list.append(float(np.percentile(a = doc[key_name]["scores_array_" + embedding_entity + "_embedding"],
                                                                  q = self.shibayama_per)))
                            except:
                                continue
                        self.corr[year][key_name + "_" + embedding_entity] = score_list 
            elif indicator =="Author_proximity":
                key_name = "Author_proximity"
                for embedding_entity in self.embedding_entities_authors:
                    for year in self.year_range:
                        self.path_doc= "Result/{}/{}".format(indicator, year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            docs = json.load(read_file)   
                        score_list_intra = []
                        score_list_inter = []
                        for doc in docs:
                            try:
                                score_list.append(float(np.percentile(a = doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_intra"],
                                                          q = self.authors_per)))
                            except:
                                continue
                            try:
                                score_list.append(float(np.percentile(a = doc[key_name]["authors_novelty_" + embedding_entity + "_profile_5"]["scores_array_inter"],
                                                          q = self.authors_per)))
                            except:
                                continue
                        self.corr[year][key_name + "_" + embedding_entity + "_5_intra"] = score_list_intra
                        self.corr[year][key_name + "_" + embedding_entity + "_5_inter"] = score_list_inter 
            elif indicator == "disruptiveness":
                key_name = "disruptiveness"
                for measure in self.disruptiveness_measures:
                    for year in self.year_range:
                        self.path_doc= "Result/Disruptiveness/{}".format(year)
                        with open(self.path_doc + ".json", "r") as read_file:
                            docs = json.load(read_file)   
                        score_list = []
                        for doc in docs:
                            try:
                                score_list.append(doc[key_name][measure])
                            except:
                                continue
                        self.corr[year][key_name + "_" + measure] = score_list
            elif self.variables:
                for variable in self.variables:
                    if indicator == 'wang':
                        for time,reu,perc in zip(self.time_window_cooc,self.n_reutilisation,self.keep_item_percentile):
                            key_name = variable + "_" + indicator + "_" + str(time) + "_" + str(reu) + "_restricted" + str(perc)
                            for year in self.year_range:
                                self.path_doc= "Result/{}/{}/{}".format(indicator, variable + "_" + str(time) + "_" + str(reu) + "_restricted" + str(perc) , year)
                                with open(self.path_doc + ".json", "r") as read_file:
                                    docs = json.load(read_file)
                                score_list = []
                                for doc in docs:
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
                                docs = json.load(read_file)
                            score_list = []
                            for doc in docs:
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
                cleaned_corr = self.corr[year][~self.corr[year].isin([np.nan, np.inf, -np.inf, None]).any(1)]
                sns.heatmap(cleaned_corr.corr(), cmap="Blues")
        else:
            cleaned_corr = pd.DataFrame()
            for year in self.year_range:
                cleaned_corr = pd.concat([cleaned_corr, self.corr[year][~self.corr[year].isin([np.nan, np.inf, -np.inf]).any(1)]], ignore_index=True)
            sns.heatmap(cleaned_corr.corr(), cmap="Blues")
                        
