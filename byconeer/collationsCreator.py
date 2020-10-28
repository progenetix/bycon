#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), pardir))
from bycon.lib.read_specs import read_named_prefs
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
        "config": read_named_prefs( "defaults", dir_path ),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "dataset_definitions",
        "filter_definitions"
    ]:
        byc.update( { d: read_named_prefs( d, dir_path ) } )

    if args.alldatasets:
        dataset_ids = byc["config"][ "dataset_ids" ]
    else:
        dataset_ids =  [ args.datasetid ]
        if not dataset_ids[0] in byc["config"][ "dataset_ids" ]:
            print("No existing dataset was provided with -d ...")
            exit()





################################################################################
################################################################################
################################################################################    

if __name__ == '__main__':
    main()
