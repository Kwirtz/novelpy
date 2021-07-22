import pandas as pd
import numpy as np
from novelpy.graphs.utils import random
import seaborn as sns

m=3

data = random().erdos_renyi(n = m)
data = random().barabasi_albert(m=m,n=100)
degrees = data.sum(axis=0)
sns.distplot(degrees, hist=False)

# inc matrix
data = np.array([3,1,1,0,-3,0,0,0,0,-1,0,-1,0,0,-1,1]).reshape(4,4)    



