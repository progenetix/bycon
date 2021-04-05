#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import cgi_parse_query,cgi_print_json_response,cgi_break_on_errors
from bycon.lib.read_specs import dbstats_return_latest, update_datasets_from_dbstats
from bycon.lib.parse_filters import select_dataset_ids, check_dataset_ids
from bycon.lib.generate_beacon_responses import return_filtering_terms, create_beacon_response, select_response_type

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import initialize_service, create_empty_service_response, populate_service_response, response_add_error, response_add_parameter, response_collect_errors, response_map_results

from byconeer.lib.schemas_parser import *


"""podmd

* <https://beacon.progenetix.org/datasets/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    filtering_terms()
    
################################################################################

def filteringTerms():
    filtering_terms()

################################################################################

def filtering_terms():

    byc = initialize_service()

    byc.update({"endpoint": "filtering_terms"})

    parse_beacon_schema(byc)
    select_dataset_ids(byc)
    check_dataset_ids(byc)

    update_datasets_from_dbstats(byc)
    
    r = create_empty_service_response(byc)

    results = return_filtering_terms(byc)

    populate_service_response( byc, r, results )
    cgi_print_json_response( byc, r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
