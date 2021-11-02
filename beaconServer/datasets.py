#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib.cgi_utils import cgi_parse_query,cgi_print_response,cgi_break_on_errors
from beaconServer.lib.read_specs import datasets_update_latest_stats
from beaconServer.lib.parse_filters import select_dataset_ids, check_dataset_ids

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import initialize_service, create_empty_service_response, populate_service_response, response_add_error,response_add_parameter,response_collect_errors

from beaconServer.lib.schemas_parser import *

"""podmd

* <https://progenetix.org/beacon/datasets/>

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

    select_dataset_ids(byc)
    check_dataset_ids(byc)
    _get_history_depth(byc)

    create_empty_service_response(byc)

    results = datasets_update_latest_stats(byc)

    populate_service_response( byc, results )
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
