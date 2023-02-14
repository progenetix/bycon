#!/usr/bin/env python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

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

    initialize_bycon_service(byc)
    r, e = instantiate_response_and_error(byc, "beaconCollectionsResponse")
    response_meta_set_info_defaults(r, byc)
    
    _get_history_depth(byc)
    dbstats = datasets_update_latest_stats(byc)

    initialize_beacon_queries(byc)

    if "beaconResultsetsResponse" in byc["response_entity"]["response_schema"]:
        create_empty_beacon_response(byc)
        byc["queries"].pop("datasets", None)
        run_result_sets_beacon(byc)
        query_results_save_handovers(byc)
    else:
        create_empty_beacon_response(byc)
        populate_service_response( byc, dbstats )

        byc["service_response"]["response"]["collections"] = byc["service_response"]["response"].pop("results", None)
        byc["service_response"]["response"].pop("result_sets", None)
        for i, d_s in enumerate(byc["service_response"]["response"]["collections"]):
            # TODO: remove verifier hack
            for t in ["createDateTime", "updateDateTime"]:
                d = str(d_s[t])
                try:
                    if re.match(r'^\d\d\d\d\-\d\d\-\d\d$', d):
                        byc["service_response"]["response"]["collections"][i].update({t:d+"T00:00:00+00:00"})
                except:
                    pass

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
