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
pkg_sub = path.dirname(__file__)
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib import *

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
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-t", "--test", help="test setting")
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    callsets_refresher()

################################################################################

def callsets_refresher():

    byc = initialize_service()
    _get_args(byc)

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    select_dataset_ids(byc)
    check_dataset_ids(byc)
    parse_filters(byc)
    parse_variants(byc)
    initialize_beacon_queries(byc)

    generate_genomic_intervals(byc)

    if len(byc["dataset_ids"]) < 1:
        print("No existing dataset was provided with -d ...")
        exit()

    generate_genomic_intervals(byc)

    for ds_id in byc["dataset_ids"]:
        _process_dataset(ds_id, byc)

################################################################################
################################################################################
################################################################################

def _process_dataset(ds_id, byc):

    no_cs_no = 0
    no_stats_no = 0

    if not ds_id in byc["config"][ "dataset_ids" ]:
        print("¡¡¡ "+ds_id+" is not a registered dataset !!!")
        return

    bios_query = {}
    if "biosamples" in byc["queries"]:
        bios_query = byc["queries"]["biosamples"]

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    bios_coll = data_db[ "biosamples" ]
    cs_coll = data_db[ "callsets" ]
    v_coll = data_db[ "variants" ]

    bs_ids = []

    for bs in bios_coll.find (bios_query, {"id":1} ):
        bs_ids.append(bs["id"])

    no =  len(bs_ids)

    bar = Bar("{} samples from {}".format(no, ds_id), max = no, suffix='%(percent)d%%'+" of "+str(no) )
    
    for bsid in bs_ids:

        bar.next()

        s = bios_coll.find_one({ "id":bsid })

        cs_ids = [ ]
        cs_query = { "biosample_id": s["id"] }

        cs_ids = cs_coll.distinct( "id", cs_query )

        if len(cs_ids) < 1:
            print("\n!!! biosample {} had no callset !!!".format(s["id"]))
            continue

        for cs in cs_coll.find( cs_query ):
            cs_ids.append(cs["id"])

            ####################################################################
            # TODO: callset stats as as function
            ####################################################################

            maps, cs_cnv_stats = interval_cnv_arrays(v_coll, { "callset_id": cs["id"] }, byc)
            # maps, cs_cnv_stats = interval_cnv_maps(v_coll, { "callset_id": cs["id"] }, byc)

            cs["info"].update({"statusmaps": maps})
            cs["info"].update({"cnvstatistics": cs_cnv_stats})

            cs_update_obj = { "info.statusmaps": maps, "info.cnvstatistics": cs_cnv_stats }

            if not byc["args"].test:
                cs_coll.update_one( { "_id": cs["_id"] }, { '$set': cs_update_obj }  )
            else:
                print(json.dumps(maps, sort_keys=True, default=str))

            ####################################################################
            ####################################################################
            ####################################################################

    bar.finish()

    print("{} {} biosamples had no callsets".format(no_cs_no, ds_id))

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
