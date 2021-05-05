#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import environ, pardir, path
import sys, datetime, argparse
from json_ref_dict import RefDict, materialize
from importlib import import_module

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *
from datasets import *

"""podmd
### Bycon - a Python-based environment for the Beacon v2 genomics API

Please see the [documentation](./doc/byconplus.md) for more information.

#### Tests

* `./bycon/byconplus.py -t`

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    # parser.add_argument("-t", "--test", action='store_true', help="test from command line with default parameters")
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-i", "--info", action='store_true', help="test from command line for info")
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    byconplus()
    
################################################################################

def byconplus():
    
    byc = initialize_service()
    _get_args(byc)

    parse_beacon_schema(byc)
        
    update_datasets_from_dbstats(byc)

    initialize_beacon_queries(byc)

    create_empty_service_response(byc)
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    beacon_get_endpoint(byc)
    parse_endpoints(byc)

    select_response_type(byc)
    check_service_requests(byc)

    beacon_respond_with_errors(byc)
    collect_dataset_responses(byc)

    create_beacon_response(byc)
    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
