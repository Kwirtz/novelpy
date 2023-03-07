import pymongo
import pandas as pd
import wosfile
import glob
import tqdm
import numpy as np
import re

class Reference_cleaner:
    
    def __init__(self,client_name,db_name,collection_name,IS_WOS):
        self.client = pymongo.MongoClient(client_name)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.mesh_col = self.db['meshterms']
        self.IS_WOS = IS_WOS
        
        
    def get_wos_J_list(self,PATH):
        '''
        

        Parameters
        ----------
        PATH : str
            Path that contains Web of Science Core Collection files from wos.

        Returns
        -------
        A merged list with journals titles abbreviations and other information on journals.

        '''
        wos_j_cores = glob.glob(PATH+'*_*.csv')
        df_wos_jcr = pd.read_csv(PATH+'wos-jcr.csv')
        df_wos_jcr = df_wos_jcr.rename(columns={'Title':'Journal title'})
        
        dfs_wos_j = pd.DataFrame()
        for wos_j in wos_j_cores:
            df_wos_j = pd.read_csv(wos_j)
            dfs_wos_j = pd.concat([dfs_wos_j,df_wos_j])
            
        self.J_list = pd.merge(df_wos_jcr,
                               dfs_wos_j.drop_duplicates(subset = ['Journal title']),
                               how= 'left',
                               on = 'Journal title')
        
            
    def get_item_year_cat(self,doc_items,item_type):
        '''
        

        Parameters
        ----------
        doc_items : list
            List of item present in CR.
        item_type : str
            'reference' or 'keyword' 
            
        Returns
        -------
        journal_cat_year : dict
            Dict with share of references labelised,
            all references year of publication,
            Web of Science Categories of the journal.

        '''

        item_list = [] 
        i=0
        
        # wether you present web of science data or pubmed knowledge graph data to the cleaner 
        if self.IS_WOS:
            for cr in doc_items:
                cr_items = cr.split(', ')
                # Be sure that there is at least 2 information for the reference
                if len(cr_items)>2:
                    
                    year = cr_items[1]
                    # TO DO :
                    # detect the journal instead of taking the 2nd item
                    journal = cr_items[2]
                    
                    # Detect the journal in Web of science journals list
                    idx = np.where(self.J_list['Title20']==journal)[0]
                    
                    # if detected add the wos category of the journal to the reference
                    if idx.size != 0:
                        i+=1
                        category = str(wosdata.J_list['Web of Science Categories'].iat[int(idx)]).split(' |')
                        item_list.append({
                            'journal':journal,
                            'year':year,
                            'category':category
                            })
                    # else capture the name and year of the journal only
                    else :
                        item_list.append({
                            'journal':journal,
                            'year':year
                            })
                # if there is only 1 information in the string consider it as the journal.
                else:
                    item_list.append({
                        'journal':cr_items[len(cr_items)-1]
                        })
        else:
            # easily extract journals and year from PKG without checking existance in WOS journal lists
            if item_type == 'reference':
                cr_pmids = []
                for cr in doc_items:
                    i+=1
                    item_list.append({
                                'journal':re.split('[.]',cr['RefCitation'])[0],
                                'year':re.split('[.]',cr['RefCitation'])[1][1:5]
                                })
                    cr_pmids.append(int(cr['RefArticleId']))
                    
            else: #elif item_type == 'keyword':
                
                for mesh in doc_items:
                    i+=1
                    descUI = mesh['DescriptorName_UI']
                    #get infos from meshterms db
                    mesh_info = self.mesh_col.find({'DescriptorUI':descUI})[0]
                    
                    if 'TreeNumberList' in mesh_info.keys():
                        cat = list({'.'.join(re.split('[.]',info)[:2]) for info in mesh_info['TreeNumberList']})
                    else:
                        cat = None
                        
                    item_list.append({
                                'descUI':descUI,
                                'year':mesh_info['DateCreated']['Year'],
                                'category': cat
                                })
                    
        if item_type == 'reference':
            var_name = 'CR_year_category'
            share_var_name = 'share_ref_captured'
        else:
            var_name = 'Mesh_year_category'
            share_var_name = 'share_mesh_captured'
        # Compute the share of references captured (only relevant for WOS)
        
        journal_cat_year = {
            share_var_name:i/len(doc_items),
            var_name: item_list
            }
        if item_type == 'reference' and not self.IS_WOS:
            journal_cat_year.update({'refs_pmids':cr_pmids})
        return journal_cat_year
        
        
        

    def wos_cr2mongo(self,PATH):
        '''
        

        Parameters
        ----------
        PATH : str
            Path that contains savedrecs files from wos.

        Returns
        -------
        Store in mongo all document that contains references (CR).

        '''
        files = glob.glob(PATH+'savedrecs*.txt')
        i=0
        docs = []
        for file in tqdm.tqdm(files):
            try:
                for doc in wosfile.records_from(file):
                    if 'CR' in doc.keys():
                        doc['PM'] = int(doc['PM'])
                        docs.append(doc)
                        i += 1
                        if i % 1000 == 0:
                            self.collection.insert_many(docs)
                            docs = []
            except Exception as e:
                print(str(e))
        self.collection.insert_many(docs)
        self.collection.create_index([ ("PM", 1) ])
        
        
        
        
    
    
    
    
    
    
    
    
