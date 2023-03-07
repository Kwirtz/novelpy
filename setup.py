from setuptools import setup, find_packages
 
classifiers = [
  'Development Status :: 5 - Production/Stable',
  'Intended Audience :: Education',
  'Operating System :: Microsoft :: Windows :: Windows 10',
  'License :: OSI Approved :: MIT License',
  'Programming Language :: Python :: 3'
]
 
setup(
  name='novelpy',
  version='1.2',
  description='Calculate novelty indicators',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',  
  author='Pelletier Pierre and Wirtz Kevin',
  author_email='kevin.wirtz@unistra.fr',
  license='MIT', 
  classifiers=classifiers,
  keywords='Novelty, scientometrics', 
  packages=find_packages(),
  install_requires=['pymongo==3.12.1','joblib==1.1.0','sklearn==1.2.1','glob2==0.7','tqdm==4.62.3',"networkx==2.5.1",'python-louvain==0.15',
  'numpy==1.19.5','pickle-mixin==1.0.2','scipy==1.5.4','pandas==1.1.5','multiprocess==0.70.12.2','pyyaml==5.4.1','spacy==3.0.0','scispacy==0.4.0','cycler==0.11.0','thinc==7.4.1',
  'wosfile==0.5','seaborn==0.11.2'] 
)
