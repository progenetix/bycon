#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir, mkdir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
import statistics
from progress.bar import Bar
import requests


# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_sub = path.dirname(__file__)
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib import *

"""

## `biosamplesRefresher`

* `biosamplesRefresher.py -d progenetix -m stats`

"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-f", "--filters", help="prefixed filter value for ext. identifier")
    parser.add_argument("-t", "--test", help="test setting")
    parser.add_argument('-i', '--inputfile', help='a custom file to specify input data')
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    biosamples_refresher()

################################################################################

def biosamples_refresher():

    byc = initialize_service()
    _get_args(byc)

    test_mode = False
    if byc["args"].test:
        test_mode = 1

    if test_mode:
        print( "¡¡¡ TEST MODE - no db update !!!")

    byc["dataset_ids"] = ["progenetix"]

    parse_filters(byc)
    parse_variants(byc)
    initialize_beacon_queries(byc)
    generate_genomic_intervals(byc)

    print("Running progenetix ...")

    no_cs_no = 0
    no_stats_no = 0
    ds_id = byc["dataset_ids"][0]
    id_filter = "GSM"
    if byc["args"].filters:
        id_filter = byc["args"].filters

    bios_query = { "$or": [
        { "external_references.id": { "$regex": id_filter } },
        { "info.legacy_id": { "$regex": id_filter } }
    ] }

    # print(bios_query)

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    bios_coll = data_db[ "biosamples" ]
    cs_coll = data_db[ "callsets" ]

    bs_ids = []

    for bs in bios_coll.find (bios_query, {"id":1 } ):
        bs_ids.append(bs["id"])

    no =  len(bs_ids)

    if not test_mode:
        bar = Bar("{} {} samples".format(no, ds_id), max = no, suffix='%(percent)d%%'+" of "+str(no) )

    counts = { "new_stages" : 0,  "new_grades" : 0 }

    platform_re = re.compile(r'^.*?(GPL\d+?)(:?[^\d]|$)', re.IGNORECASE)
    series_re = re.compile(r'^.*?(GSE\d+?)(:?[^\d]|$)', re.IGNORECASE)
    experiment_re = re.compile(r'^.*?(GSM\d+?)(:?[^\d]|$)', re.IGNORECASE)

    for bsid in bs_ids:

        get_geosoft = True
        gsm = False
        gse = False
        gsm_soft = False

        # TODO: Read in files if existing ... 
        # To be added after some collection exists

        s = bios_coll.find_one({ "id":bsid })

        # if not "tumor_stage" in s["info"]:
        #     get_geosoft = True

        update_obj = {
            "analysis_info": {
                "experiment_id": "",
                "platform_id": "",
                "series_id": ""
            },
            "info": s["info"]
        }

        if "external_references" in s:
            for e_r in s[ "external_references" ]:
                if "GSM" in e_r["id"]:
                    update_obj["analysis_info"].update({"experiment_id":e_r["id"]})
                    gsm = experiment_re.match(e_r["id"]).group(1)
                if "GSE" in e_r["id"]:
                    update_obj["analysis_info"].update({"series_id":e_r["id"]})
                    gse = series_re.match(e_r["id"]).group(1)
                if "GPL" in e_r["id"]:
                    update_obj["analysis_info"].update({"platform_id":e_r["id"]})

        if gse is False or gsm is False:

            print("\n{} did not have GEO ids in external_references!!".format(bsid))
            continue
        
        gse_path = path.join( pkg_path, *byc["config"]["paths"]["geosoft_file_root"], gse )
        gsm_path = path.join( gse_path, gsm+".txt" )

        if path.isfile(gsm_path):               
            with open(gsm_path) as f:                        
                gsm_soft = f.readlines()
        else:
            gsm_soft = retrieve_geosoft_file(gsm, byc)
            if not path.isdir(gse_path):
                mkdir(gse_path)
            s_f = open(gsm_path, 'w')
            for l in gsm_soft:
                s_f.write(l)
            s_f.close()

        # getting rid of data header and some verbose stuff
        gsm_soft = list(filter(lambda x:'Sample_' in x, gsm_soft))
        gsm_soft = list(filter(lambda x:'_protocol' not in x, gsm_soft))

        geosoft_retrieve_tumor_stage(gsm, gsm_soft, update_obj, byc, counts)
        geosoft_retrieve_tumor_grade(gsm, gsm_soft, update_obj, byc, counts)

        for l in gsm_soft:

            if "!Sample_platform_id" in l:
                update_obj["analysis_info"].update({"platform_id": "geo:"+platform_re.match(l).group(1)}) 
            if "!Sample_series_id" in l:
                update_obj["analysis_info"].update({"series_id": "geo:"+series_re.match(l).group(1)})

            series_id = series_re.match(update_obj["analysis_info"]["series_id"]).group(1)

        if not test_mode:
            bios_coll.update_one( { "_id": s["_id"] }, { '$set': update_obj }  )
            bar.next()
        else:
            print(update_obj)


    if not byc["args"].test:
        bar.finish()

    for k, n in counts.items():
        print("=> updated {}: {}".format(k, n))

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
