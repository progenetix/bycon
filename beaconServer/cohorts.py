#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

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

    byc = initialize_service()

    select_dataset_ids(byc)
    check_dataset_ids(byc)
    _get_history_depth(byc)

    create_empty_service_response(byc)

    results = datasets_update_latest_stats(byc, "cohorts")

    populate_service_response( byc, results )
    byc["service_response"]["response"]["collections"] = byc["service_response"]["response"].pop("results")
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
