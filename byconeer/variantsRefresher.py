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
from beaconServer.lib.read_specs import *
from beaconServer.lib.parse_filters import *

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import initialize_service

"""

## `biosamplesRefresher`

"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    parser.add_argument("-t", "--test", help="test setting")
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    variants_refresher()

################################################################################

def variants_refresher():

    byc = initialize_service()
    _get_args(byc)

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    if len(byc["dataset_ids"]) < 1:
        print("No existing dataset was provided with -d ...")
        exit()

    mongo_client = MongoClient( )

    min_l = byc["this_config"]["refreshing"]["cnv_min_length"]

    for ds_id in byc["dataset_ids"]:

        v_short = 0
        v_no_type = 0

        data_db = mongo_client[ ds_id ]
        var_coll = data_db[ "variants" ]
        no =  var_coll.estimated_document_count()
        bar = Bar("{} vars".format(ds_id), max = no, suffix='%(percent)d%%'+" of "+str(no) )
        for v in var_coll.find({}):
            update_obj = { "id": str(v["_id"]) }

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
                            update_obj.update( { "info.var_length": cnv_l } )
                    except:
                        update_obj.update( { "error.start_end": 1 } )
                else:
                    v_no_type += 1
                    # update_obj.update( { "error.variant_type": v["variant_type"] } )
            else:
                v_no_type += 1
                print("!!! no type".format(v["_id"]))

            ####################################################################

            if not byc["args"].test:
                var_coll.update_one( { "_id": v["_id"] }, { '$set': update_obj }  )
            
            bar.next()
        bar.finish()

        print("{} {} variants had no type {}".format(v_no_type, ds_id, min_l))
        print("{} {} CNV variants had a length below {}".format(v_short, ds_id, min_l))

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
