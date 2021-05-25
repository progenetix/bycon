#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
from progress.bar import Bar
import time
import numpy as np

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
    min_f = byc["interval_definitions"]["interval_min_fraction"]
    int_no = len(byc["genomic_intervals"])

    for coll in coll_coll.find(id_query):

        coll_i += 1

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

        update_obj = {
            "id": coll["id"],
            "label": coll["label"],
            "child_terms": coll["child_terms"],
            "updated": date_isoformat(datetime.datetime.now()),
            "counts": {"biosamples": bios_no, "callsets": cs_no },
            "frequencymap": {
                "intervals": int_no,
                "binning": byc["genome_binning"],
                "sample_count": cs_no
            }
        }

        i_fs = byc["genomic_intervals"].copy()

        fFactor = 100 / cs_no;
        i_t = coll_i % 100

        start_time = time.time()
        if i_t == 0 or cs_no > 1000:
            print("{}: {} bios, {} cs\t{}/{}\t{:.1f}%".format(coll["id"], bios_no, cs_no, coll_i, coll_no, 100*coll_i/coll_no))

        pars = {
            "gain": {"cov_l": "dup", "val_l": "max" },
            "loss": {"cov_l": "del", "val_l": "min" }
        }

        for t in pars.keys():

            covs = np.zeros( (cs_no, int_no) )
            vals = np.zeros( (cs_no, int_no) )

            for i, cs in enumerate(callsets.rewind()):
                covs[i] = cs["info"]["statusmaps"][ pars[t]["cov_l"] ]
                vals[i] = cs["info"]["statusmaps"][ pars[t]["val_l"] ]

            counts = np.count_nonzero(covs >= min_f, axis=0)
            frequencies = np.around(counts * fFactor, 3)
            medians = np.around(np.ma.median(np.ma.masked_where(covs < min_f, vals), axis=0).filled(0), 3)
            means = np.around(np.ma.mean(np.ma.masked_where(covs < min_f, vals), axis=0).filled(0), 3)

            for i, interval in enumerate(i_fs):
                i_fs[i].update( {
                    t+"_frequency": frequencies[i],
                    t+"_median": medians[i],
                    t+"_mean": means[i]
                } )

        update_obj["frequencymap"].update({"intervals": i_fs})

        proc_time = time.time() - start_time
        if cs_no > 1000:
            print(" => Processed in {:.2f}s: {:.4f}s per callset".format(proc_time, (proc_time/cs_no)))

        if not byc["args"].test:
            fm_coll.update_one( { "id": coll["id"] }, { '$set': update_obj }, upsert=True )

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
