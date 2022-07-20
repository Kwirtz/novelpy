import argparse
import yaml
parser = argparse.ArgumentParser(
    description='50 chunks')

parser.add_argument('-year')
args = parser.parse_args()
#skip_ = int(args.skip_)
year = int(args.year)



from novelpy import Disruptiveness

disruptiveness = Disruptiveness(
   client_name = 'mongodb://Pierre:ilovebeta67@localhost:27017',
   db_name =  'novelty_final',
   collection_name = 'Citation_network',
   focal_year = year,
   id_variable = 'PMID',
   refs_list_variable ='refs',
   cits_list_variable ='cited_by',
   year_variable = 'year')


disruptiveness.get_indicators(parallel = False)
