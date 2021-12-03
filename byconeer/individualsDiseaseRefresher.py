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
"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-t", "--test", help="test setting")
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    individuals_refresher()

################################################################################

def individuals_refresher():

    byc = initialize_service()
    _get_args(byc)

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    ds_id = byc["dataset_ids"][0]

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    bios_coll = data_db[ "biosamples" ]
    ind_coll = data_db[ "individuals" ]

    bios_no = bios_coll.estimated_document_count()

    bar = Bar("Writing ", max = bios_no, suffix='%(percent)d%%'+" of "+str(bios_no) )

    ind_no = 0

    for bios in bios_coll.find ({}):

        bar.next()

        ind = ind_coll.find_one({"id":bios["individual_id"]})
        if ind is False:
            continue

        update_obj = {
            "diseases": [],
            "vital_status": {
                "status": "UNKNOWN_STATUS"
            },
        }

        for k in update_obj.keys():
            if k in ind:
                update_obj.update({k: ind[k] })

        if not "reference" in bios["biosample_status"]["label"]:

            ind_no += 1

            disease = {
                "disease_code": bios.get("histological_diagnosis", {}),
                "stage": bios.get("pathological_stage", {}),
                "clinical_tnm_finding": bios.get("pathological_tnm_findings", []),
                "followup_state": bios.get("followup_state", {}),
                "followup_time": bios["info"].get("followup_months", None)
            }

            if disease["followup_time"] is not None:
                update_obj["vital_status"].update({"survival_time_in_days": int(disease["followup_time"] * 30.25) })
                disease.update({"followup_time": "P"+str(disease["followup_time"])+"M" })

            try:
                disease.update({"age_of_onset": bios["time_of_collection"].get("age", {})})
            except:
                pass

            try:
                if "alive" in disease["followup_state"]["label"]:
                    update_obj["vital_status"].update({"status":"ALIVE"})
            except:
                pass
            try:
                if "dea" in disease["followup_state"]["label"]:
                    update_obj["vital_status"].update({"status":"DECEASED"})
            except:
                pass

            update_obj["diseases"].append(disease)

        if not byc["args"].test:
            ind_coll.update_one( { "_id": ind["_id"] }, { '$set': update_obj }  )

    bar.finish()

    print("=> diseases for {} individuals".format(ind_no))

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
