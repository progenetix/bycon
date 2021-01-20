#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
import statistics
from progress.bar import Bar

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.read_specs import *
"""

## `biosamplesRefresher`

"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    parser.add_argument("-t", "--test", help="test setting")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    service = "variants"

    byc = {
        "pkg_path": pkg_path,
        "args": _get_args(),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "config",
        "dataset_definitions"
    ]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

    # first pre-population w/ defaults
    these_prefs = read_local_prefs( service, dir_path )
    for d_k, d_v in these_prefs.items():
        byc.update( { d_k: d_v } )

################################################################################

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    if byc["args"].alldatasets:
        dataset_ids = byc["config"][ "dataset_ids" ]
    else:
        dataset_ids =  byc["args"].datasetids.split(",")
        if not dataset_ids[0] in byc["config"][ "dataset_ids" ]:
            print("No existing dataset was provided with -d ...")
            exit()

    mongo_client = MongoClient( )

    min_l = byc["refreshing"]["cnv_min_length"]

    for ds_id in dataset_ids:
        if not ds_id in byc["config"][ "dataset_ids" ]:
            print("¡¡¡ "+ds_id+" is not a registered dataset !!!")
            continue

        v_short = 0
        v_no_type = 0

        data_db = mongo_client[ ds_id ]
        var_coll = data_db[ "variants" ]
        no =  var_coll.estimated_document_count()
        if not byc["args"].test:
            bar = Bar("Refreshing {} vars".format(ds_id), max = no, suffix='%(percent)d%%'+" of "+str(no) )
        for v in var_coll.find({}):
            update_obj = { }
            """
 
            """
            if "variant_type" in v:
                if "DUP" in v["variant_type"] or "DEL" in v["variant_type"]:
                    try:
                        cnv_l = int( v["end"] - v["start"])
                        if cnv_l < min_l:
                            v_short += 1
                            if byc["args"].test:
                                print("!!! too short {}".format(cnv_l))
                            else:
                                var_coll.delete_one( { "_id": v["_id"] }  )
                                continue
                        else:
                            update_obj.update( { "info.cnv_length": cnv_l } )
                    except:
                        update_obj.update( { "error.start_end": 1 } )
                else:
                    v_no_type += 1
                    update_obj.update( { "error.variant_type": v["variant_type"] } )
            else:
                v_no_type += 1
                print("!!! no type".format(v["_id"]))

            ####################################################################

            if not byc["args"].test:
                var_coll.update_one( { "_id": v["_id"] }, { '$set': update_obj }  )
                bar.next()

        if not byc["args"].test:
            bar.finish()

        print("{} {} variants had no type {}".format(v_no_type, ds_id, min_l))
        print("{} {} CNV variants had a length below {}".format(v_short, ds_id, min_l))

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
