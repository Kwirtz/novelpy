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
  version='0.1',
  description='Calculate novelty indicators',
  long_description=open('README.txt').read() + '\n\n' + open('CHANGELOG.txt').read(),
  url='',  
  author='Pierre Pelletier and Wirtz Kevin',
  author_email='kevin.wirtz@unistra.fr',
  license='MIT', 
  classifiers=classifiers,
  keywords='Novelty, scientometrics', 
  packages=find_packages(),
  install_requires=['pymongo','joblib','sklearn','glob2','tqdm','networkx','python-louvain',
  'numpy','pickle-mixin','scipy','pandas','tqdm','multiprocess'] 
)
