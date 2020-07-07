#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path as path
from os import environ
import sys, os, datetime, argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""podmd
### Bycon - a Python-based environment for the Beacon v2 genomics API

Please see the [documentation](./doc/byconplus.md) for more information.

#### Tests

* from parent directory `./bin/byconplus.py -t -n`

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-t", "--test", action='store_true', help="test from command line with default parameters")
    parser.add_argument("-i", "--info", action='store_true', help="test from command line for info")
    parser.add_argument("-n", "--filtering_terms", action='store_true', help="test filtering term response")
    args = parser.parse_args()

    return(args)

################################################################################

def main():
    byconplus()
    
################################################################################

def byconplus():
    
    config = read_bycon_config( path.abspath( dir_path ) )

    # TODO: "byc" becoming a proper object?!
    byc = {
        "config": config,
        "args": _get_args(),
        "form_data": cgi_parse_query(),
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "variant_defs": read_variant_definitions( **config[ "paths" ] ),
        "datasets_info": read_datasets_info( **config[ "paths" ] ),
        "service_info": read_service_info( **config[ "paths" ] ),
        "beacon_info": read_beacon_info( **config[ "paths" ] ),
        "beacon_paths": read_beacon_api_paths( **config[ "paths" ] ),
        "h->o": read_handover_info( **config[ "paths" ] ),
        "dbstats": dbstats_return_latest( **config ),
        "get_filters": False
    }

    byc["beacon_info"].update( { "datasets": update_datasets_from_dbstats(**byc) } )
    for par in byc[ "beacon_info" ]:
        byc[ "service_info" ][ par ] = byc[ "beacon_info" ][ par ]

    byc.update( { "endpoint": beacon_get_endpoint(**byc) } )
    byc.update( { "endpoint_pars": parse_endpoints( **byc ) } )
    byc.update( { "response_type": select_response_type( **byc ) } )

    byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
    byc.update( { "filters":  parse_filters( **byc ) } )

    check_service_requests(**byc)

    # adding arguments for querying / processing data
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    byc.update( { "queries": beacon_create_queries( **byc ) } )

    # fallback - but maybe shouldbe an error response?
    if not byc[ "queries" ].keys():
        cgi_print_json_response(byc["service_info"])

    # TODO: There should be a better place for this ...
    if len(byc[ "dataset_ids" ]) < 1:
        cgi_exit_on_error("No `datasetIds` parameter provided.")

    byc.update( { "dataset_responses": collect_dataset_responses(**byc) } )
    beacon_response = create_beacon_response(**byc)
    
    cgi_print_json_response(beacon_response)

################################################################################
################################################################################

if __name__ == '__main__':
    main()
