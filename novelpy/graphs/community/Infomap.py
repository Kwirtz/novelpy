from novelpy.indicators.our_indicator import *
import infomap
from collections import defaultdict
import itertools

class Infomap_based_indicator(our_indicator):

    def networkx2infomap(self,graph):
        im = infomap.Infomap()
        _ = [im.add_node(node) for node in graph]
        _ = [im.add_link(edge[0], edge[1],edge[2]["weight"]) for edge in graph.edges(data=True)]
        self.im = im
    
    def get_community(self):
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
        
        self.im.run()


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
            self.networkx2infomap(self.subgraph)
            self.get_community()
            communities = defaultdict(list)
            for node in self.im.tree:
                if node.is_leaf:
                    communities[node.module_id].append(node.node_id)
            for community in communities:
                community_appartenance = [i for i in itertools.combinations(communities[community], r=2)]
                for i in community_appartenance:
                    self.df.at[i[0], i[1]] += 1
                    self.df.at[i[1], i[0]] += 1    