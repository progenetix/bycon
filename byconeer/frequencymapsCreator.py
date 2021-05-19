#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
from progress.bar import Bar

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib import *
from services.lib import *
"""

## `frequencymapsCreator`

"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    parser.add_argument("-t", "--test", help="test setting")
    parser.add_argument("-p", "--prefixes", help="selected prefixes")
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():
    frequencymaps_creator()

################################################################################

def frequencymaps_creator():

    byc = initialize_service()
    _get_args(byc)

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    select_dataset_ids(byc)
    check_dataset_ids(byc)
    parse_variants(byc)

    if len(byc["dataset_ids"]) < 1:
        print("No existing dataset was provided with -d ...")
        exit()

    if byc["args"].prefixes:
        byc.update({"filters": re.split(",", byc["args"].prefixes)})

    generate_genomic_intervals(byc)
 
    for ds_id in byc["dataset_ids"]:
        print( "Creating collations for " + ds_id)
        _create_frequencymaps_for_collations( ds_id, **byc )

################################################################################

def _create_frequencymaps_for_collations( ds_id, **byc ):

    coll_client = MongoClient()
    coll_coll = coll_client[ ds_id ][ byc["config"]["collations_coll"] ]

    fm_client = MongoClient()
    fm_coll = fm_client[ ds_id ][ byc["config"]["frequencymaps_coll"] ]
    print(byc["config"]["frequencymaps_coll"])

    bios_client = MongoClient()
    bios_coll = bios_client[ ds_id ][ byc["config"]["collations_source"] ]

    data_client = MongoClient()
    cs_coll = data_client[ ds_id ]["callsets"]

    id_query = {}

    if "filters" in byc:
        if len(byc["filters"]) > 0:
            f_l = []
            for pre in byc["filters"]:
                f_l.append( { "id": { "$regex": "^"+pre } })
            if len(f_l) > 1:
                id_query = { "$or": f_l }
            else:
                id_query = f_l[0]

    coll_no = coll_coll.count_documents(id_query)
   
    bar = Bar("Writing {} {} fMaps".format(coll_no, ds_id), max = coll_no, suffix='%(percent)d%%'+" of "+str(coll_no) )

    for coll in coll_coll.find(id_query):

        bar.next()

        bios_query = { "$or": [
            { "biocharacteristics.id": { '$in': coll["child_terms"] } },
            { "cohorts.id": { '$in': coll["child_terms"] } },
            { "external_references.id": { '$in': coll["child_terms"] } }
        ] }

        bios_ids = bios_coll.distinct( "id" , bios_query )
        bios_no = len(bios_ids)

        cs_query = { "biosample_id": { "$in": bios_ids } }

        cs_no = cs_coll.count_documents(cs_query)
        callsets = cs_coll.find(cs_query)

        if cs_no < 1:
            continue

        cnvmaps = [ ]

        for cs in callsets:
            if "dupcoverage" in cs["info"]["statusmaps"]:
                cnvmaps.append(cs["info"]["statusmaps"])

        update_obj = {
            "id": coll["id"],
            "label": coll["label"],
            "child_terms": coll["child_terms"],
            "updated": date_isoformat(datetime.datetime.now()),
            "counts": {"biosamples": bios_no, "callsets": len(cnvmaps) },
            "frequencymaps": interval_cnv_frequencies(cnvmaps, byc)
        }

        # print("{}: {} samples".format(coll["id"], bios_no))

        if not byc["args"].test:
            fm_coll.update_one( { "id": coll["id"] }, { '$set': update_obj }, upsert=True )


    bar.finish()

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
