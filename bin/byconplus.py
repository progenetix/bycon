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
    args = parser.parse_args()

    return args

################################################################################

def main():

    byconplus("byconplus")
    
################################################################################

def byconplus(service):
    
    config = read_bycon_config( path.abspath( dir_path ) )

    # TODO: "byc" becoming a proper object?!
    byc = {
        "config": config,
        "args": _get_args(),
        "form_data": cgi_parse_query(),
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "geolocations": read_named_prefs( "geolocations", dir_path ),
        "variant_defs": read_named_prefs( "variant_definitions", dir_path ),
        "datasets_info": read_yaml_with_key_to_object( "beacon_datasets_file", "datasets", **config[ "paths" ] ),
        "service_info": read_yaml_with_key_to_object( "service_info_file", "service_info", **config[ "paths" ] ),
        "beacon_info": read_yaml_with_key_to_object( "beacon_info_file", "beacon_info", **config[ "paths" ] ),
        "beacon_paths": read_yaml_with_key_to_object( "beacon_paths_file", "paths", **config[ "paths" ] ),
        "h->o": read_named_prefs( "beacon_handovers", dir_path ),
        "errors": [ ],
        "warnings": [ ],
        "dbstats": dbstats_return_latest( **config )
    }

    byc["beacon_info"].update( { "datasets": update_datasets_from_dbstats(**byc) } )
    for par in byc[ "beacon_info" ]:
        byc[ "service_info" ][ par ] = byc[ "beacon_info" ][ par ]

    byc.update( { "endpoint": beacon_get_endpoint(**byc) } )
    byc.update( { "endpoint_pars": parse_endpoints( **byc ) } )
    byc.update( { "response_type": select_response_type( **byc ) } )

    byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
    byc.update( { "dataset_ids": beacon_check_dataset_ids( **byc ) } )
    byc.update( { "filter_flags": get_filter_flags( **byc ) } )
    byc.update( { "filters": parse_filters( **byc ) } )

    check_service_requests(**byc)

    # adding arguments for querying / processing data
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    byc.update( { "queries": create_queries( **byc ) } )

    beacon_respond_with_errors( **byc )

    byc.update( { "dataset_responses": collect_dataset_responses(**byc) } )
    beacon_response = create_beacon_response(**byc)
    
    cgi_print_json_response( byc["form_data"], beacon_response, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
