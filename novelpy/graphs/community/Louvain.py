# pip install python-louvain
import community as community_louvain
from novelpy.indicators.our_indicator import *
from collections import defaultdict
import itertools

class Louvain_based_indicator(our_indicator):
    
    def get_community(self,graph):
        '''
        Description
        -----------
        
        perform a community algorithm on the graph g
        
        Parameters
        ----------

        Returns
        -------
        Partition of the graph

        '''
        
        partition = community_louvain.best_partition(graph, partition=None, weight='weight', resolution=1.0, randomize=None, random_state=None)
        return partition

    def community_appartenance(self):
            '''
            Description
            -----------
            
            Add 1 in the adjacency matrix at the location of two nodes that were in the same community
            in the get_community function
            
            Parameters
            ----------
    
            Returns
            -------
            The Adjacency matrix
    
            '''
            partition = self.get_community(self.subgraph)
            communities = defaultdict(list)
            for key, value in sorted(partition.items()):
                communities[value].append(key)
            for community in communities:
                community_appartenance = [i for i in itertools.combinations(communities[community], r=2)]
                for i in community_appartenance:
                    self.df[i[0], i[1]] += 1
                    self.df[i[1], i[0]] += 1    