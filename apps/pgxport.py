#!/usr/local/bin/python3

from pymongo import MongoClient
import sys, getopt, yaml
from os import path as path

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

with open( path.join(path.abspath(dir_path), '..', "config", "pgxport.yaml") ) as cf:
    config = yaml.full_load( cf )
config[ "paths" ][ "out"] = path.join(path.abspath(dir_path), '..', "data", "out")

########################################################################################################################
########################################################################################################################
########################################################################################################################

def main(argv):

    kwargs = { "config": config }
    opts, args = get_cmd_args(argv)
    queries = pgx_queries_from_args(opts, **kwargs)
    kwargs[ "config" ][ "plot_pars" ] = plotpars_from_args(opts, **kwargs)
    kwargs[ "config" ][ "data_pars" ] = pgx_datapars_from_args(opts, **kwargs)

    if not queries:
        print('No query specified; please use "-h" for examples')
        sys.exit( )

    kwargs = { "config": config, "queries": queries }
    query_results = execute_bycon_queries(**kwargs)

    kwargs = { "config": config, "callsets::_id": query_results["callsets::_id"] }
    write_callsets_matrix_files(**kwargs)

    kwargs = { "config": config, "callsets::_id": query_results["callsets::_id"] }
    callsets_stats = return_callsets_stats(**kwargs)

    kwargs = { "config": config, "callsets_stats": callsets_stats }
    plot_callset_stats(**kwargs)

########################################################################################################################
########################################################################################################################
########################################################################################################################

if __name__ == '__main__':
    main( sys.argv[ 1: ] )
