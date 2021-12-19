#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd

* <https://progenetix.org/beacon/cohorts/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    datasets()

################################################################################

def collections():

    datasets()
    
################################################################################

def datasets():

    byc = initialize_service()
    
    _get_history_depth(byc)
    dbstats = datasets_update_latest_stats(byc)

    beacon_get_endpoint_base_paths(byc)
    initialize_beacon_queries(byc)

    if "beaconResultsetsResponse" in byc["response_entity"]["response_schema"]:
        create_empty_service_response(byc)
        byc["queries"].pop("datasets", None)
        run_result_sets_beacon(byc)
        query_results_save_handovers(byc)
    else:
        create_empty_service_response(byc)
        populate_service_response( byc, dbstats )
        byc["service_response"]["response"]["collections"] = byc["service_response"]["response"].pop("results", None)
        for i, d_s in enumerate(byc["service_response"]["response"]["collections"]):
            # TODO: remove verifier hack
            for t in ["createDateTime", "updateDateTime"]:
                d = str(d_s[t])
                try:
                    if re.match(r'^\d\d\d\d\-\d\d\-\d\d$', d):
                        byc["service_response"]["response"]["collections"][i].update({t:d+"T00:00:00+00:00"})
                except:
                    pass

    # byc["service_response"]["response"]["result_sets"] = byc["service_response"]["response"].pop("results")
    cgi_print_response( byc, 200 )

################################################################################

def _get_history_depth(byc):

    if "statsNumber" in byc["form_data"]:
        s_n = byc["form_data"]["statsNumber"]
        try:
            s_n = int(s_n)
        except:
            pass
        if type(s_n) == int:
            if s_n > 0:
                byc.update({"stats_number": s_n})
    return byc

################################################################################
################################################################################

if __name__ == '__main__':
    main()
