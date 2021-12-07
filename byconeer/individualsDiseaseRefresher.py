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

    f_u_def = { "id": "EFO:0030039", "label": "no followup status" }
    age_def = { "age": "" }
    stage_def = { "id": "NCIT:C92207", "label": "Stage Unknown"}

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

        # for k in update_obj.keys():
        #     if k in ind:
        #         update_obj.update({k: ind[k] })

        if not "reference" in bios["biosample_status"]["label"]:

            ind_no += 1

            disease = {
                "disease_code": bios.get("histological_diagnosis", {}),
                "stage": bios.get("pathological_stage", {}),
                "clinical_tnm_finding": bios.get("pathological_tnm_findings", []),
                "followup_state": bios.get("followup_state", {}),
                "followup_time": bios["info"].get("followup_months", None),
                "age_of_onset": bios.get("time_of_collection", age_def)
            }

            if not "id" in disease["stage"]:
                disease.update({"stage": stage_def})
            if not "id" in disease["followup_state"]:
                disease.update({"followup_state": f_u_def})
            if not "age" in disease["age_of_onset"]:
                disease.update({"age_of_onset": age_def})

            if disease["followup_time"] is not None:
                update_obj["vital_status"].update({"survival_time_in_days": int(disease["followup_time"] * 30.25) })
                disease.update({"followup_time": "P"+str(disease["followup_time"])+"M" })

            try:
                disease.update({"age_of_onset": bios.get("time_of_collection", {})})
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

            d_k_s = list(disease.keys())
            for d_k in d_k_s:
                if disease[d_k] == {}:
                    disease.pop(d_k, None)

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
