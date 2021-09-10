import community as community_louvain
from novelpy.indicators.utils_foster2015 import *
from collections import defaultdict
import itertools

class Foster2015(community_appartenance):
    
    def Louvain_based(self):
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
            print("Get Partition of community ...")
            partition = community_louvain.best_partition(self.g, partition=None, weight='weight', resolution=1.0, randomize=None, random_state=None)
            print("Partition Done !")
            communities = defaultdict(list)
            for key, value in sorted(partition.items()):
                communities[value].append(key)
            for community in communities:
                community_appartenance = [i for i in itertools.combinations(communities[community], r=2)]
                for i in community_appartenance:
                    i = sorted(i)
                    self.df[i[0], i[1]] += 1