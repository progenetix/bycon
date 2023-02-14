#!/usr/bin/env python3

import cgi, cgitb, sys, os, datetime, re, json, yaml
from os import environ, pardir, path
from pymongo import MongoClient

# local
pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""podmd

* <https://progenetix.org/beacon/datasets/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    cohorts()

################################################################################

def collections():

    cohorts()
    
################################################################################

def cohorts():

    initialize_bycon_service(byc)
    run_beacon_init_stack(byc)
    return_filtering_terms_response(byc)

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
        return byc

    mongo_client = MongoClient( )

    cohorts =  []

    # TODO: verifier hack ...
    if not "cohorts" in byc["queries"]:
        byc.update({"test_mode": True})

    if byc["test_mode"] is True:
        byc["queries"].update( {"cohorts": { "collation_type": "pgxcohort" } } )

    try:
        query = byc["queries"]["cohorts"]
        
        for ds_id in byc[ "dataset_ids" ]:
            mongo_db = mongo_client[ ds_id ]        
            mongo_coll = mongo_db[ "collations" ]

            for cohort in mongo_coll.find( query ):
                cohorts.append(cohort)
                byc["service_response"]["response_summary"].update({"exists":True})
    except:
        pass

    cohorts = remap_cohorts(cohorts, byc)

    byc["service_response"]["response"].pop("result_sets", None)
    byc["service_response"]["response"].update({"collections": cohorts})
    byc["service_response"]["response_summary"].update({"num_total_results":len(cohorts)})
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
