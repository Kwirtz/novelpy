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
  version='1.4',
  description='Calculate novelty indicators',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',  
  author='Pelletier Pierre and Wirtz Kevin',
  author_email='kevin.wirtz@unistra.fr',
  license='MIT', 
  classifiers=classifiers,
  keywords='Novelty, scientometrics', 
  packages=find_packages(),
  install_requires=['spacy==3.7.2','pymongo==4.6.1','scikit-learn==1.4.0','glob2==0.7',"networkx==3.2.1",'python-louvain==0.16',
  'pickle-mixin==1.0.2','pandas==2.1.4','multiprocess==0.70.16','pyyaml==6.0.1','wosfile==0.6','seaborn==0.13.2'] 
)

