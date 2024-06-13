import os
import tqdm
import json
import scipy
import pickle 
import numpy as np
import json
import novelpy
import unittest
import math


class TestLee(unittest.TestCase):
    
    def get_papers_items(self):

        self.papers_item = {5:["A", "C", "D"],#NEWCOMB
                               6:["B", "C", "B"]
                              }

        self.lee = novelpy.Lee2015(collection_name = 'Ref_journals',
                                    id_variable = 'id',
                                    year_variable = 'year',
                                    variable = 'Ref_journals',
                                    sub_variable = 'item',
                                    focal_year = 3,
                                    density = True)
    
    def test_get_data(self):
        self.get_papers_items()
        self.lee.get_data()

        self.assertDictEqual(d1 = self.lee.papers_items,d2 = self.papers_item)

    def test_compute_comb_score(self):
        self.get_papers_items()
        self.lee.get_data()
        self.lee.compute_comb_score()
        print(self.lee.current_adj.A)
        N = 1+1+1+2+1
        adj_mat = np.array([[0,0,1,1],
                            [0,1,2,0],
                            [0,0,0,1],
                            [0,0,0,0]])

        Ni_mat = np.array([[2,2,2,2],
                            [3,3,3,3],
                            [4,4,4,4],
                            [2,2,2,2]])
        Nj_mat = np.array([[2,3,4,2],
                            [2,3,4,2],
                            [2,3,4,2],
                            [2,3,4,2]])
        numerator = adj_mat*N
        divider = np.multiply(Ni_mat,Nj_mat)
        comb_scores_test = np.divide(numerator,divider)

        comb_scores = pickle.load(open(self.lee.path_score + "/{}.p".format(self.lee.focal_year),"rb" ) ).A
        np.testing.assert_array_equal(comb_scores,comb_scores_test)


    def test_update_paper_values(self):
        self.get_papers_items()
        self.lee.get_data()
        self.lee.compute_comb_score()
        self.lee.update_paper_values()
        score = json.load(open(self.lee.path_output+ "/{}.json".format(self.lee.focal_year),"r" ))
        test_score = [{"id": 5,
                      "Ref_journals_lee": {"scores_array": [0.75,1.5,0.75], 
                                            "score": {"novelty": -np.log(np.quantile([0.75,1.5,0.75],0.1))}}},
                     {"id": 6,
                      "Ref_journals_lee": {"scores_array": [1.0,2/3,1.0], 
                                            "score": {"novelty": -np.log(np.quantile([1,2/3,1],0.1))}}}
                    ]
        json.dump(test_score,open(self.lee.path_output+ "/{}_test.json".format(self.lee.focal_year),"w" ))
        test_score = json.load(open(self.lee.path_output+ "/{}_test.json".format(self.lee.focal_year),"r" ))
        self.assertListEqual(score,test_score)

"""
for i in range(0,200):
    
    # Define the size of the matrix
    matrix_size = 5
    
    # Generate random values for the upper triangular part
    upper_triangular = np.random.random((matrix_size, matrix_size))
    
    # Make the upper triangular part symmetric by copying it to the lower triangular part
    symmetric_matrix = upper_triangular + upper_triangular.T - np.diag(upper_triangular.diagonal())
    
    # Specify the number of zeros to introduce
    num_zeros = 5
    
    # Randomly select positions for zeros
    zero_positions = np.random.choice(range(matrix_size ** 2), size=num_zeros, replace=False)
    
    # Set the selected positions to zero
    row_indices, col_indices = np.unravel_index(zero_positions, (matrix_size, matrix_size))
    symmetric_matrix[row_indices, col_indices] = 0
    symmetric_matrix[col_indices, row_indices] = 0
    matrix = csr_matrix(symmetric_matrix)
    
    Nt = np.sum(triu(matrix))
    temp_adj = matrix
    ij_sums = sp.csr_matrix(np.sum(temp_adj.A, axis= 0)[np.newaxis], dtype=np.int64)
    ij_products = ij_sums.T.dot(ij_sums)
    test2 = (csr_matrix(temp_adj,dtype=float)*int(Nt))/ij_products
    

    
    test = sp.lil_matrix((temp_adj.shape[0], temp_adj.shape[1]), dtype=np.float64)
    nonzero_rows, nonzero_cols = temp_adj.nonzero()
    for row, col in tqdm.tqdm(zip(nonzero_rows, nonzero_cols)):
        value = temp_adj[row, col]
        ij_products = ij_sums[0,row]*ij_sums.T[col,0]
        test[row,col] = value*int(Nt)/ij_products
    test = csr_matrix(test)
    
    test.data[np.isinf(test.data)] =  0
    test.data[np.isnan(test.data)] =  0
    test = triu(test,format='csr')

    test2[np.isinf(test2)] =  0
    test2[np.isnan(test2)] =  0
    test2 = triu(test2,format='csr')
    
    are_same = np.array_equal(test.toarray(), test2.toarray())
    
    # Print the result
    if are_same:
        print("ok")
    else:
        print(test.toarray(),test2)


current_adj =  pickle.load( open('G:/Github/ai_research/Data/cooc/concepts/weighted_network_self_loop/1997.p', "rb" )) 
Nt = np.sum(triu(current_adj))
temp_adj = current_adj.T+triu(current_adj,k=1)
ij_sums = sp.csr_matrix(np.sum(temp_adj.A, axis= 0)[np.newaxis], dtype=np.int64)


result = sp.lil_matrix((current_adj.shape[1], current_adj.shape[1]), dtype=np.float64)
nonzero_rows, nonzero_cols = temp_adj.nonzero()
for row, col in tqdm.tqdm(zip(nonzero_rows, nonzero_cols)):
    value = temp_adj[row, col]
    ij_products = ij_sums[0,row]*ij_sums[0,row]
    result[row,col] = value*int(Nt)/ij_products
"""