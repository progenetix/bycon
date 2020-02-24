#!/usr/local/bin/python3

# podmd
#
# python3 pgxport.py -j '{
#   "biosamples": {"external_references.type.id": {"$regex":"CVCL" } },
#   "callsets": {"info.cnvstatistics.cnvfraction": {"$gt": 0} }
# }'
# python3 pgxport.py -j '{
#   "biosamples": {"external_references.type.id": {"$regex":"CVCL" } }, "callsets": {"info.cnvstatistics.cnvfraction": {"$gt": 0},"info.statusmaps.dupmax":{"$gt":0} }, "variants": { "reference_name": "22" } }'
# python3 pgxport.py -a 0.2 -j '{
#         "biosamples": { "biocharacteristics.type.id": {"$regex":"icdom-[98]" } },
#         "callsets": {  },
#         "variants": { "reference_name": "9", "variant_type": "DEL", "$and": [ {"start": { "$lt": 21975098 } }, {"start": { "$gt": 18000000 } } ], "$and": [ { "end": { "$gt": 21967753 } }, { "end": { "$lt": 26000000 } } ] }
# }'
# pgxport.py -a 0.1 -j '{
#         "biosamples": { "biocharacteristics.type.id": {"$regex":"icdom-[98]" } },
# }'
# end_podmd

from pymongo import MongoClient
import sys, getopt
from os import path as path

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

# TODO: defaults to config file
config = {}
config[ "const" ] =  { "tab_sep": "\t", "dash_sep": "-" }
config[ "paths" ] = { "out": path.join(path.abspath(dir_path), '..', "data", "out") }
config[ "dataset_ids" ] = { "biosamples","callsets","individuals","variants","querybuffer" }
config[ "bio_prefixes" ] = { 'icdom', 'icdot', 'ncit' }
config[ "paths" ]["status_matrix_file_label"] = 'matrix_status.tsv'
config[ "paths" ]["values_matrix_file_label"] = 'matrix_values.tsv'
config[ "plot_pars" ] = { "dotalpha": 0.2 }
config[ "data_pars" ] = { "dataset_id": "arraymap" }

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
        print('no query')
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
