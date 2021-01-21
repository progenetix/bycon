#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import environ, pardir, path
import sys, datetime, argparse

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib import *
from byconeer.lib.schemas_parser import *
from services.lib.service_utils import *

"""podmd
### Bycon - a Python-based environment for the Beacon v2 genomics API

Please see the [documentation](./doc/byconplus.md) for more information.

#### Tests

* `./bycon/byconplus.py -t`

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-t", "--test", action='store_true', help="test from command line with default parameters")
    parser.add_argument("-i", "--info", action='store_true', help="test from command line for info")
    args = parser.parse_args()

    return args

################################################################################

def main():

    byconplus("byconplus")
    
################################################################################

def byconplus(service):
    
    byc = initialize_service(service)

    update_datasets_from_dbstats(byc)

    beacon_get_endpoint(byc)
    parse_endpoints(byc)

    select_response_type(byc)

    select_dataset_ids(byc)
    beacon_check_dataset_ids(byc)

    get_filter_flags(byc)  
    parse_filters(byc)

    check_service_requests(byc)

    parse_variants(byc)
    get_variant_request_type(byc)
    generate_queries(byc)

    beacon_respond_with_errors(byc)
    collect_dataset_responses(byc)   
    create_beacon_response(byc)    
    cgi_print_json_response(
        byc["form_data"],
        create_beacon_response(byc),
        200
    )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
