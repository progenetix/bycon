#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.read_specs import read_bycon_configs_by_name
"""

## `collationsCreator`

"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetid", help="dataset")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    byc = {
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "dataset_definitions",
        "filter_definitions"
    ]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

    if args.alldatasets:
        dataset_ids = byc["config"][ "dataset_ids" ]
    else:
        dataset_ids =  [ args.datasetid ]
        if not dataset_ids[0] in byc["config"][ "dataset_ids" ]:
            print("No existing dataset was provided with -d ...")
            exit()

################################################################################

    for ds_id in dataset_ids:
        
        coll_terms = dataset_count_collationed_filters(ds_id, **byc)
        coll_types = byc["config"]["collationed"]

        for pre in coll_types.keys():
            # create /retrieve hierarchy tree; method to be developed
            hier = get_prefix_hierarchy(pre, **byc)


################################################################################

def get_prefix_hierarchy(pre, **byc):

    hier = [ ]

    h_p = 
    
    return hier

################################################################################
################################################################################
################################################################################    

if __name__ == '__main__':
    main()
