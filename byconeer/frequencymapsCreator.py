#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
from progress.bar import Bar
import time

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
   
    print("Writing {} {} fMaps".format(coll_no, ds_id))

    coll_i = 0

    for coll in coll_coll.find(id_query):

        coll_i += 1

        bios_query = _make_child_terms_query(coll)
        bios_no, cs_cursor = _cs_cursor_from_bios_query(bios_coll, cs_coll, bios_query)
        cs_no = len(list(cs_cursor))

        if cs_no < 1:
            continue

        i_t = coll_i % 100
        start_time = time.time()
        if i_t == 0 or cs_no > 1000:
            print("{}: {} bios, {} cs\t{}/{}\t{:.1f}%".format(coll["id"], bios_no, cs_no, coll_i, coll_no, 100*coll_i/coll_no))

        intf = interval_counts_from_callsets(cs_cursor, byc)

        update_obj = {
            "id": coll["id"],
            "label": coll["label"],
            "child_terms": coll["child_terms"],
            "updated": date_isoformat(datetime.datetime.now()),
            "counts": {"biosamples": bios_no, "callsets": cs_no },
            "frequencymap": {
                "interval_count": len(byc["genomic_intervals"]),
                "binning": byc["genome_binning"],
                "biosample_count": bios_no,
                "analysis_count": cs_no,
                "intervals": intf
            }
        }

        if coll["code_matches"] > 0:
            if cs_no != coll["code_matches"]:
                bios_query = _make_exact_query(coll)
                bios_no, cs_cursor = _cs_cursor_from_bios_query(bios_coll, cs_coll, bios_query)
                cs_no = len(list(cs_cursor))
                intf = interval_counts_from_callsets(cs_cursor, byc)

                print("found {} exact code matches".format(cs_no))

            update_obj.update({ "frequencymap_codematches": {
                    "interval_count": len(byc["genomic_intervals"]),
                    "binning": byc["genome_binning"],
                    "biosample_count": bios_no,
                    "analysis_count": cs_no,
                    "intervals": intf
                }
            })

        proc_time = time.time() - start_time
        if cs_no > 1000:
            print(" => Processed in {:.2f}s: {:.4f}s per callset".format(proc_time, (proc_time/cs_no)))

        if not byc["args"].test:
            fm_coll.update_one( { "id": coll["id"] }, { '$set': update_obj }, upsert=True )


################################################################################

def _make_exact_query(coll):

    return { "$or": [
            { "biocharacteristics.id": coll["id"] },
            { "cohorts.id": coll["id"] },
            { "external_references.id": coll["id"] }
        ] }

################################################################################

def _make_child_terms_query(coll):

    return { "$or": [
            { "biocharacteristics.id": { '$in': coll["child_terms"] } },
            { "cohorts.id": { '$in': coll["child_terms"] } },
            { "external_references.id": { '$in': coll["child_terms"] } }
        ] }

################################################################################

def _cs_cursor_from_bios_query(bios_coll, cs_coll, query):

    bios_ids = bios_coll.distinct( "id" , query )
    bios_no = len(bios_ids)
    cs_query = { "biosample_id": { "$in": bios_ids } }
    cs_cursor = cs_coll.find(cs_query)

    return bios_no, cs_cursor

################################################################################



################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
