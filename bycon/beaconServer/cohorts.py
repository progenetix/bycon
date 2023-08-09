#!/usr/bin/env python3

import cgi, sys, os, datetime, re, json, yaml
from os import environ, pardir, path
from pymongo import MongoClient

from bycon import *

"""podmd

* <https://progenetix.org/beacon/datasets/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        cohorts()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)

################################################################################

def collections():

    try:
        cohorts()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)
    
################################################################################

def cohorts():

    initialize_bycon_service(byc)
    run_beacon_init_stack(byc)

    _return_cohorts_response(byc)

    run_result_sets_beacon(byc)
    query_results_save_handovers(byc)
    check_computed_interval_frequency_delivery(byc)
    check_switch_to_count_response(byc)
    check_switch_to_boolean_response(byc)
    cgi_print_response( byc, 200 )

################################################################################

def _return_cohorts_response(byc):

    if not "cohort" in byc["response_entity_id"]:
        return

    mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))

    cohorts =  []
    c_id = byc.get("request_entity_path_id_value")
 
    if c_id is not None:
        query = { "id": c_id }
    else:
        query = { "collation_type": "pgxcohort" }
    
    for ds_id in byc[ "dataset_ids" ]:
        mongo_db = mongo_client[ ds_id ]        
        mongo_coll = mongo_db[ "collations" ]

        for cohort in mongo_coll.find( query ):
            cohorts.append(cohort)
            byc["service_response"]["response_summary"].update({"exists":True})

    cohorts = remap_cohorts(cohorts, byc)

    if byc["test_mode"] is True:
        ret_no = int(byc.get('test_mode_count', 5))
        cohorts = cohorts[:ret_no]

    byc["service_response"]["response"].pop("result_sets", None)
    byc["service_response"]["response"].update({"collections": cohorts})
    byc["service_response"]["response_summary"].update({"num_total_results":len(cohorts)})
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
