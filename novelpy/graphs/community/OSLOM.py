from argparse import Namespace
import oslom

# run OSLOM with data in Python objects
args = Namespace()
args.min_cluster_size = 0
args.oslom_exec = oslom.DEF_OSLOM_EXEC
args.oslom_args = oslom.DEF_OSLOM_ARGS

# edges is an iterable of tuples (source, target, weight)
# in the same format as the command-line version
edges = [(0, 1, 1.0), (1, 2, 1), (2, 0, 1)]
#clusters = oslom.run_in_memory(args, edges)
#print(clusters)