import os
import glob
import json
import tqdm
import pickle
import pymongo
import numpy as np
from collections import Counter
from itertools import combinations

class Dataset:
    
    def __init__(self,
             client_name = None,
             db_name = None,
             collection_name = None,
             id_variable = None,
             year_variable = None,
             variable = None,
             sub_variable = None,
             focal_year = None,
             time_window_cooc = None,
             n_reutilisation = None,
             starting_year = None,
             new_infos = None,
             density = False,
             keep_item_percentile = None,
             list_ids = None):
        """
        Description
        -----------
        Class that returns items list for each paper and the adjacency matrix for the focal year.
        Also returns item info depending of indicator.
        
        Parameters
        ----------


        client_name : str, optional
            client name. The default is None.
        db_name : str, optional
            db name. The default is None.
        collection_name : str, optional
            collection name. The default is None.        
        id_variable : str
            id variable name. 
        year_variable : str
            year variable name.
        variable : str
            variable of interest.
        sub_variable : str, optional
            subvariable of interest. The default is None.
        focal_year : int
            year of interest.
        time_window_cooc: int
            Sum the coocurence between the t-time_window_cooc and t+time_window_cooc
        density: bool
            Store scores' density 
        Returns
        -------
        None.
    
        """
        
        self.client_name = client_name
        self.db_name = db_name
        self.collection_name = collection_name
        self.id_variable = id_variable
        self.year_variable = year_variable
        self.variable = variable
        self.sub_variable = sub_variable
        self.focal_year = focal_year
        self.time_window_cooc = time_window_cooc
        self.n_reutilisation = n_reutilisation
        self.starting_year = starting_year
        self.new_infos = new_infos
        self.item_name = self.variable.split('_')[0] if self.variable else None
        self.density  = density
        self.keep_item_percentile = keep_item_percentile
        self.list_ids = list_ids
        
        if self.client_name:
            self.client = pymongo.MongoClient(client_name)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]

        self.restricted = '_restricted{}'.format(self.keep_item_percentile) 
    

    def get_q_journal_list(self):
        items = []
        for year in tqdm.tqdm(range(self.focal_year-3,self.focal_year)):
            if self.client_name:
                self.docs = self.collection.find({
                    self.variable:{'$exists':'true'},
                    self.year_variable:year
                    })
            else:
                self.docs = json.load(open("Data/docs/{}/{}.json".format(self.collection_name,
                                                                         year)) )
            for doc in self.docs:
                if self.variable in doc:
                    for ref in doc[self.variable]:
                        items.append(ref[self.sub_variable])

        count = Counter(items)                
        nb_cit = [count[item] for item in count]
        percentile = np.percentile(nb_cit,self.keep_item_percentile)
        self.list_of_items_restricted = [item for item in count if count[item] >= percentile]

    def get_item_infos(self,
                       item):
        """
   
        Description
        -----------        
        Get item info depedning on the indicator

        Parameters
        ----------
        item : dict
            item from a document list of items.
        indicator : str
            indicator for which the score is computed.

        Returns
        -------
        doc_item : dict/list
            dict or list depending on the indicator structured as needed for later usage.

        """
     
        if self.indicator == 'uzzi':
            if 'year' in item.keys():
                doc_item = {'item':item[self.sub_variable],
                                  'year':item['year']}
        elif self.indicator == 'kscores': 
            doc_item = item
        else:
            doc_item = item[self.sub_variable]
        
        return  doc_item
        
    
    def get_item_paper(self):
        """
        
        Description
        -----------        
        Get items info depedning on the indicator for all documents in a given year
        
        Parameters
        ----------
        indicator : str
            indicator for which the score is computed.

        Returns
        -------
        papers_items: dict
            dict with document id and item strucutured as needed

        """
        
        # Get docs where variable of interest exists and published in focal_year
        if self.client_name:
            self.docs = self.collection.find({
                self.variable:{'$exists':'true'},
                self.year_variable:self.focal_year
                })
        else:
            self.docs = json.load(open("Data/docs/{}/{}.json".format(self.collection_name,self.focal_year)) )
        
        # dict of every docs. Each one contains doc_items
        self.papers_items = dict()


        for doc in tqdm.tqdm(self.docs, desc = "get_papers_item"):
            if self.list_ids:
                if doc[self.id_variable] in self.list_ids:
                    if self.sub_variable:
                        doc_items = list()
                        for item in doc[self.variable]:
                            doc_item = self.get_item_infos(item)
                            if doc_item:
                                doc_items.append(doc_item)
        
                        self.papers_items.update({int(doc[self.id_variable]):doc_items})  
                    else:
                        self.papers_items.update({int(doc[self.id_variable]):doc[self.variable]})
            else:
                if self.sub_variable:
                    doc_items = list()
                    for item in doc[self.variable]:
                        doc_item = self.get_item_infos(item)
                        if doc_item:
                            doc_items.append(doc_item)
    
                    self.papers_items.update({int(doc[self.id_variable]):doc_items})  
                else:
                    self.papers_items.update({int(doc[self.id_variable]):doc[self.variable]})                    

    def sum_cooc_matrix(self, window = None):
        """
        
    
        Parameters
        ----------
        time_window : int
            time window to compute the difficulty in the past and the reutilisation in the futur.
        path : str
            path to adjacency matrices.
    
        Returns
        -------
        matrix : scipy.sparse.csr.csr_matrix
            sum of considered matrices.
    
        """
        
        
        i = 0
        if window:
            for year in window:
                if i == 0:
                    cooc = pickle.load(open( self.path_input + "/{}.p".format(year), "rb" ))
                    i += 1
                else:
                    cooc += pickle.load(open( self.path_input + "/{}.p".format(year), "rb" ))
        else: 
            files = glob.glob(self.path_input+ "/*")
            files = [file for file in files if file.split("\\")[-1].split(".")[0] not in ["index2name","name2index"]]
            files = [file for file in files if file.split("/")[-1].split(".")[0] not in ["index2name","name2index"]]
            try:
                files = [file for file in files if int(file.split("\\")[-1].split(".")[0])<self.focal_year]
            except:
                files = [file for file in files if int(file.split("/")[-1].split(".")[0])<self.focal_year]
            for file in tqdm.tqdm(files,desc="Summing cooc"):
                if i == 0:
                    cooc = pickle.load(open( file, "rb" ))
                    i += 1
                else:
                    cooc += pickle.load(open( file, "rb" ))                
        return cooc

    def get_cooc(self):
        
        unw = ['wang']
        type1 = 'unweighted_network' if self.indicator in unw else 'weighted_network'
        type2 = 'no_self_loop' if self.indicator in unw else 'self_loop'
        self.path_input = "Data/cooc/{}/{}_{}".format(self.variable,type1,type2)
        self.name2index = pickle.load(open(self.path_input + "/name2index.p", "rb" ))
        
        if self.indicator == "foster":
            if self.starting_year:
                self.current_adj = self.sum_cooc_matrix( window = range(self.starting_year, self.focal_year))
            else:
                print("loading cooc")
                self.current_adj = self.sum_cooc_matrix()
                
        elif self.indicator == "wang":
            print("Calculate past matrix ")
            if self.starting_year:
                self.past_adj = self.sum_cooc_matrix( window = range(self.starting_year, self.focal_year))
            else:
                self.past_adj = self.sum_cooc_matrix()
            print('Calculate futur matrix')
            self.futur_adj = self.sum_cooc_matrix(window = range(self.focal_year+1, self.focal_year+self.time_window_cooc+1))

            print('Calculate difficulty matrix')
            self.difficulty_adj = self.sum_cooc_matrix(window = range(self.focal_year-self.time_window_cooc,self.focal_year))
        else:
            self.current_adj =  pickle.load( open(self.path_input+'/{}.p'.format(self.focal_year), "rb" )) 
        

    def get_data(self):
        
        if self.indicator in ['uzzi','wang','lee',"foster"]:
            # Get the coocurence for self.focal_year
            print("loading cooc for focal year {}".format(self.focal_year))
            self.get_cooc()
            print("cooc loaded !")
            print("loading items for papers in {}".format(self.focal_year))    
            # Dict of paper, for each paper a list of item that appeared
            self.get_item_paper()
            print("items_loaded !")    


class create_output(Dataset):

    def get_paper_score(self):
        """
    
        Description
        -----------
        Compute scores for a document and store indicators scores in a dict
    
        Parameters
        ----------
        kwargs : keyword arguments
            More argument for novelty as time_window or n_reutilisation
    
        Returns
        -------
        dict
            scores and indicators infos.
    
        """



        if self.unique_pairwise and self.keep_diag:
            combis = [(i,j) for i,j in combinations(set(self.current_items),2)]
        elif self.unique_pairwise == False and self.keep_diag == False:
            combis = [(i,j) for i,j in combinations(self.current_items,2) if i != j]
        elif self.unique_pairwise and self.keep_diag == False:
            combis = [(i,j) for i,j in combinations(set(self.current_items),2) if i != j]
        else:
            combis = [(i,j) for i,j in combinations(self.current_items,2)]
        
        scores_list = []
        for combi in combis:
            if self.indicator == 'wang':
                if self.list_of_items_restricted:
                    if combi[0] in self.list_of_items_restricted and combi[1] in self.list_of_items_restricted: 
                        combi = sorted( (self.name2index[combi[0]], self.name2index[combi[1]]) )
                        scores_list.append(float(self.comb_scores[combi[0], combi[1]]))
            else:
                combi = sorted( (self.name2index[combi[0]], self.name2index[combi[1]]) )
                scores_list.append(float(self.comb_scores[combi[0], combi[1]]))
            """
            comb_infos.append({"item1" : combi[0],
                          "item2" : combi[1],
                          "score" : float(self.comb_scores[combi[0], combi[1]]) })
            """
        self.scores_array = np.array(scores_list)
        
        key = self.variable + '_' + self.indicator
        if self.n_reutilisation and self.time_window_cooc:
            key = key +'_'+str(self.time_window_cooc)+'_'+str(self.n_reutilisation)+self.restricted
        elif self.time_window_cooc:
            key = key +'_'+str(self.time_window_cooc)+self.restricted
           
        if self.indicator == 'wang':
            score = {'novelty':sum(self.scores_array)}
            
        elif self.indicator == 'uzzi':
            score = {'conventionality': np.median(self.scores_array),
                     'novelty': np.quantile(self.scores_array,0.1)}
            
        elif self.indicator == 'lee':
            score = {'novelty': -np.log(np.quantile(self.scores_array,0.1))}
        
        elif self.indicator == 'foster':
            scores_list = [1-i for i in self.scores_array]
            score = {'novelty': float(np.mean(scores_list))}

        if self.density:
            doc_infos = {"scores_array": scores_list,
                         'score':score}
        else:
            doc_infos = {'score':score}

        self.key = key
        self.doc_infos = doc_infos
        return {key:doc_infos}
    
    def populate_list(self):
        """
        Description
        -----------
    
        Parameters
        ----------
        Returns
        -------
        Update on mongo paper scores or store it in a dict
    
        """
        
        # Load the score of pairs given by the indicator
        if self.indicator == 'wang':
            self.comb_scores = pickle.load(
                    open(
                        'Data/score/{}/{}/{}.p'.format(
                            self.indicator,
                            self.variable+'_'+str(self.time_window_cooc)+'_'+str(self.n_reutilisation)+self.restricted,
                             self.focal_year),
                        "rb" ))       
        else:
            self.comb_scores = pickle.load(
                    open(
                        'Data/score/{}/{}/{}.p'.format(
                            self.indicator,self.variable,self.focal_year),
                        "rb" ))  
        
        # Iterate over every docs 
        list_of_insertion = []
        for idx in tqdm.tqdm(list(self.papers_items),desc='start'):
        
            if self.indicator in ['uzzi','wang','lee','foster']:
                # Check that you have more than 2 item (1 combi) else no combination and no novelty 
                if len(self.papers_items[idx])>2:
                    self.current_items = self.papers_items[idx]
                    
                    if self.indicator == 'uzzi':
                        self.current_items = [item["item"] for item in self.current_items]
                    
                    if self.indicator != 'wang':
                        self.unique_pairwise = False
                        self.keep_diag=True
                    else:
                        self.unique_pairwise = True
                        self.keep_diag=False
                                   
                    # Use novelty score of combination + Matrix of combi of papers to have novelty score of the paper with id_variable = idx
                    self.get_paper_score()
                else:
                    continue
            
            elif self.new_infos:
                self.doc_infos = self.new_infos
            
            
            if self.client_name:
                list_of_insertion.append({self.id_variable: int(idx),
                                          self.key: self.doc_infos,
                                          self.year_variable:self.focal_year})
            else:
                list_of_insertion.append({self.id_variable: int(idx),self.key: self.doc_infos, self.year_variable:self.focal_year})

        
        if self.client_name:
            self.collection_output.insert_many(list_of_insertion)
        else:
            with open(self.path_output + "/{}.json".format(self.focal_year), 'w') as outfile:
                json.dump(list_of_insertion, outfile)        
    
    def update_paper_values(self, **kwargs):
        """

        Description
        -----------        
        run database update

        Parameters
        ----------
        **kwargs : keyword arguments, optional
            More argument for novelty as time_window or n_reutilisation.
            
        Returns
        -------
        None.

        """
        if self.client_name:
                self.collection_output_name = "output_" + self.indicator + "_" + self.variable
                if self.indicator == "wang":
                    self.collection_output_name = "output_" + self.indicator + "_" + self.variable + "_" + str(self.time_window_cooc) + "_" + str(self.n_reutilisation)+self.restricted
                self.collection_output = self.db[self.collection_output_name]
                if self.collection_output_name not in self.db.list_collection_names():
                    print("Init output collection with index on id_variable ...")
                    self.collection_output.create_index([ (self.id_variable,1) ])
                    self.collection_output.create_index([ (self.year_variable,1) ])
        else:
            if self.indicator == "wang":
                self.path_output = "Result/{}/{}".format(self.indicator, self.variable+ "_" + str(self.time_window_cooc) + "_" + str(self.n_reutilisation)+self.restricted)
            else:
                self.path_output = "Result/{}/{}".format(self.indicator, self.variable)
            if not os.path.exists(self.path_output):
                os.makedirs(self.path_output)
                
        if self.indicator in ['uzzi','lee','wang','foster']:
            self.populate_list()
        else:
            print('''indicator must be in 'uzzi', 'foster', 'lee', 'wang' ''')
        print('saved')
