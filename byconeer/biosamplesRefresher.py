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
from bycon.lib.read_specs import *
from lib.schemas_parser import *

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

    service = "biosamples"

    byc = {
        "pkg_path": pkg_path,
        "pkg_sub": pkg_sub,
        "args": _get_args(),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "config",
        "dataset_definitions",
        "filter_definitions"
    ]:
        read_bycon_configs_by_name( d, byc )

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

    no_cs_no = 0
    no_stats_no = 0

    for ds_id in dataset_ids:

        if not ds_id in byc["config"][ "dataset_ids" ]:
            print("¡¡¡ "+ds_id+" is not a registered dataset !!!")
            continue

        data_db = mongo_client[ ds_id ]
        bios_coll = data_db[ "biosamples" ]
        cs_coll = data_db[ "callsets" ]
        no =  bios_coll.estimated_document_count()
        if not byc["args"].test:
            bar = Bar("Refreshing {} samples".format(ds_id), max = no, suffix='%(percent)d%%'+" of "+str(no) )
        for s in bios_coll.find({}):

            """
            The following code will refresh callset ids and their statistics into
            the biosamples entries.
            If no callsets are found this will result in empty attributes; if
            more than one callset is found the average of the CNV statistics will be used.
            """

            cs_ids = [ ]
            cnv_stats = { }
            cnvstatistics = {k:[] for k in byc["refreshing"]["cnvstatistics"]}
            cs_query = { "biosample_id": s["id"] }
            for cs in cs_coll.find( cs_query ):
                cs_ids.append(cs["id"])
                for s_k in cnvstatistics.keys():
                    if s_k in cs["info"]["cnvstatistics"]:
                        cnvstatistics[ s_k ].append(cs["info"]["cnvstatistics"][ s_k ])
            any_stats = False
            if len(cs_ids) > 0:
                for s_k in cnvstatistics.keys():
                    n = len(cnvstatistics[ s_k ])
                    if n > 0:
                        any_stats = True
                        cnv_stats[ s_k ] = sum(cnvstatistics[ s_k ]) / n
                        if cnv_stats[ s_k ] < 1:
                            cnv_stats[ s_k ] = round( cnv_stats[ s_k ], 3)
                        else:
                            cnv_stats[ s_k ] = int( cnv_stats[ s_k ] )
            else:
                no_cs_no += 1

            if not any_stats:
                no_stats_no += 1

            update_obj = { "info.callset_ids": cs_ids, "info.cnvstatistics": cnv_stats }

            """
            --- other biosample modification code
            """

            if "sampledTissue" in s:
                if "UBERON" in s["sampledTissue"]["id"]:
                    biocs = [ s["sampledTissue"] ]
                    for b_c in s[ "biocharacteristics" ]:
                        if not "UBERON" in b_c["id"]:
                            biocs.append(b_c)
                    update_obj.update( { "biocharacteristics": biocs } )

            if "biocharacteristics" in s:
                for b_c in s[ "biocharacteristics" ]:
                     if "NCIT:C" in b_c["id"]:
                        update_obj.update( { "histological_diagnosis": b_c } ) 

            ####################################################################

            if not byc["args"].test:
                bios_coll.update_one( { "_id": s["_id"] }, { '$set': update_obj }  )
                bar.next()

        if not byc["args"].test:
            bar.finish()

        print("{} {} biosamples had no callsets".format(no_cs_no, ds_id))
        print("{} {} biosamples received no CNV statistics".format(no_stats_no, ds_id))         

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
