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

"""podmd
### Bycon - a Python-based environment for the Beacon v2 genomics API

Please see the [documentation](./doc/byconplus.md) for more information.

#### Tests

* from parent directory `./bycon/byconplus.py -t`

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
    
    # TODO: "byc" becoming a proper object?!
    byc = {
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        "args": _get_args(),
        "form_data": cgi_parse_query(),
        "errors": [ ],
        "warnings": [ ]
    }

    for d in [
        "dataset_definitions",
        "filter_definitions",
        "geoloc_definitions",
        "variant_definitions",
        "handover_definitions"
    ]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

    for p in ["service_info", "beacon_info", "beacon_paths"]:
        byc.update( { p: read_local_prefs( p, dir_path ) } )

    byc.update( { "dbstats": dbstats_return_latest( **byc ) } )

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
    byc.update( { "queries": generate_queries( **byc ) } )

    beacon_respond_with_errors( **byc )

    byc.update( { "dataset_responses": collect_dataset_responses(**byc) } )
    beacon_response = create_beacon_response(**byc)
    
    cgi_print_json_response( byc["form_data"], beacon_response, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
