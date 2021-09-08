# WoS query TS=(Novelty indicator) Or TS=(Bibliometric indicator) Or TS=(Scientometric indicator)  Or TS=(Bibliometric indicators) Or TS=(Scientometric indicators) Or TS=(Novelty indicators) 
# https://www-webofscience-com.scd-rproxy.u-strasbg.fr/wos/woscc/summary/8461559b-6000-4f92-9523-32ea755aecf8-046a7d45/relevance/1
import glob
import wosfile
from collections import defaultdict
import tqdm
import pandas as pd
import matplotlib.pyplot as plt

files = glob.glob("D:/kevin_data/WoS_novelpy/savedrecs*.txt")

date = defaultdict(int)
for rec in tqdm.tqdm(wosfile.records_from(files)):
    if rec.get("PY") != None:
        date[int(rec.get("PY"))] += 1
    
df = pd.DataFrame(date,index=[0])
df = df.reindex(sorted(df.columns), axis=1)

fig, ax = plt.subplots(1, 1, figsize=(3, 2), dpi=300)
df.T[:-1].plot(ax = ax, lw=1.5,title="Number of publication per year")
ax.set_ylabel("Number of publication")
ax.set_xlabel("Year")
ax.get_legend().remove()
plt.savefig('D:/Github/novelpy/Paper/publication.png')

