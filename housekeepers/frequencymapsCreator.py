#!/usr/bin/env python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
from progress.bar import Bar
import time

from bycon import *
from bycon.services import bycon_bundler, interval_utils, collation_utils, service_helpers

"""
## `frequencymapsCreator`
"""

################################################################################
################################################################################
################################################################################

def main():
    frequencymaps_creator()

################################################################################

def frequencymaps_creator():
    initialize_bycon_service()
    interval_utils.generate_genome_bins()
    service_helpers.ask_limit_reset()

    if len(BYC["BYC_DATASET_IDS"]) > 1:
        print("Please give only one dataset using -d")
        exit()

    ds_id = BYC["BYC_DATASET_IDS"][0]
    collation_utils.set_collation_types()
    print(f'=> Using data values from {ds_id} for {BYC.get("genomic_interval_count", 0)} intervals...')

    data_client = MongoClient(host=DB_MONGOHOST)
    data_db = data_client[ ds_id ]
    coll_coll = data_db[ "collations" ]
    fm_coll = data_db[ "frequencymaps" ]
    ind_coll = data_db["individuals"]
    bios_coll = data_db[ "biosamples" ]
    cs_coll = data_db["analyses"]

    coll_ids = _filter_coll_ids(coll_coll)    
    coll_no = len(coll_ids)
   
    if not BYC["TEST_MODE"]:
        bar = Bar(f'{coll_no} {ds_id} fMaps', max = coll_no, suffix='%(percent)d%%'+f' of {coll_no}' )

    coll_i = 0

    for c_id in coll_ids:
        coll = coll_coll.find_one({"id": c_id})
        c_o_id = coll.get("_id")
        if not coll:
            print(f"\n¡¡¡ some error - collation {c_id} not found !!!")
            if not BYC["TEST_MODE"]:
                bar.next()
            continue
        coll_i += 1

        start_time = time.time()

        # prdbug(coll)

        BYC.update({"BYC_FILTERS":[{"id":c_id}, {"id": "EDAM:operation_3961"}]})
        BYC.update({"PAGINATED_STATUS": False})
        BYC.update({"FMAPS_SCOPE": coll.get("scope", "biosamples")})
        
        prdbug(f'=> processing {c_id} with limit {BYC_PARS.get("limit")}')
        RSS = ByconResultSets().datasetsResults()
        pdb = bycon_bundler.ByconBundler().resultsets_frequencies_bundles(RSS)
        if_bundles = pdb.get("interval_frequencies_bundles")

        if not BYC["TEST_MODE"]:
            bar.next()

        if len(if_bundles) < 1:
            prdbug(f'No interval_frequencies for {c_id}')
            continue

        analyses_count = RSS[ds_id]["analyses.id"]["target_count"]
        cnv_cs_count = if_bundles[0].get("sample_count", 0)

        coll_coll.update_one(
            {"_id": c_o_id},
            {"$set": {"cnv_analyses": analyses_count}}
        )
        if cnv_cs_count < 1:
            continue


        update_obj = {
            "id": c_id,
            "label": coll["label"],
            "dataset_id": coll["dataset_id"],
            "scope": coll["scope"],
            "db_key": coll["db_key"],
            "collation_type": coll["collation_type"],
            "child_terms": coll["child_terms"],
            "updated": datetime.datetime.now().isoformat(),
            "frequencymap": {
                "interval_count": BYC["genomic_interval_count"],
                "binning": BYC_PARS.get("genome_binning", ""),
                "intervals": if_bundles[0].get("interval_frequencies", []),
                "frequencymap_samples": cnv_cs_count,
                "cnv_analyses": analyses_count
            }
        }

        if cnv_cs_count > 2000:
            proc_time = time.time() - start_time
            print(f'\n==> Processed {c_id}: {cnv_cs_count} of {analyses_count} in {"%.2f" % proc_time}s: {"%.4f" % (proc_time/cnv_cs_count)}s per analysis')

        if not BYC["TEST_MODE"]:
            fm_coll.delete_many( { "id": c_id } )
            fm_coll.insert_one( update_obj )

    if not BYC["TEST_MODE"]:
        bar.finish()


################################################################################

def _filter_coll_ids(coll_coll):
    # collation types have been limited potentially before
    f_d_s = BYC.get("filter_definitions", {})
    c_t_s = list(f_d_s.keys())
    query = { "collation_type":{"$in": c_t_s } }
    if len(BYC["BYC_FILTERS"]) > 0:
        f_l = []
        for c_t in BYC["BYC_FILTERS"]:
            f_l.append( c_t["id"])
        if len(f_l) > 1:
            query = { "$and": [
                            { "collation_type":{"$in": c_t_s }},
                            { "id": {"$in": f_l }}
                        ]
                    }
        elif len(f_l) == 1:
            query = { "$and": [
                            {"collation_type":{"$in": c_t_s }},
                            {"id": f_l[0]}
                        ]
                    }

    coll_ids = coll_coll.distinct("id", query)

    return coll_ids


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
