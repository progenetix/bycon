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

bycon_lib_path = path.join( pkg_path, "bycon", "lib" )
sys.path.append( bycon_lib_path )

from cgi_utils import cgi_break_on_errors, cgi_print_json_response
from generate_beacon_responses import beacon_respond_with_errors, check_service_requests, collect_dataset_responses, create_beacon_response, select_response_type
from handover_execution import retrieve_handover, handover_return_data
from handover_generation import query_results_save_handovers
from parse_beacon_endpoints import beacon_get_endpoint, parse_endpoints
from parse_filters import select_dataset_ids, check_dataset_ids, get_filter_flags, parse_filters
from parse_variants import parse_variants, get_variant_request_type
from query_execution import execute_bycon_queries
from query_generation import generate_queries
from read_specs import update_datasets_from_dbstats

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import initialize_service, create_empty_service_response, populate_service_response, response_add_error, response_add_parameter, response_collect_errors, response_map_results

from byconeer.lib.schemas_parser import *

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

    # for s in ["biosamples","variants"]:
    #     if s in byc["response_type"]:
    #         mod = import_module(s)
    #         serv = getattr(mod, s)
    #         serv(s)

    # exclude_keys = [ "format", "examples", "description", "example", "required" ]
    # empty_meta = create_empty_instance( materialize(byc["beacon-schema"]["components"]["schemas"]["BiosampleResponse"]["properties"]["meta"]["properties"], exclude_keys = exclude_keys) )
    # empty_resp = create_empty_instance( materialize(byc["beacon-schema"]["components"]["schemas"]["BiosampleResponse"]["properties"]["response"]["properties"], exclude_keys = exclude_keys) )
    # print( json.dumps({ "meta": empty_meta, "response": empty_resp }, indent=4, sort_keys=True, default=str)+"\n")

    # r = create_empty_service_response(byc)
    # for p in ["api_version", "beacon_id"]: 
    #     r["meta"].update({p: byc["beacon_info"][ snake_to_camel(p) ]})

    # print( json.dumps(r, indent=4, sort_keys=True, default=str)+"\n")

    # exit()

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    get_filter_flags(byc)  
    parse_filters(byc)

    check_service_requests(byc)

    parse_variants(byc)
    get_variant_request_type(byc)
    generate_queries(byc)

    beacon_respond_with_errors(byc)
    collect_dataset_responses(byc)

    # r = create_empty_service_response(byc)
    # for p in ["api_version", "beacon_id"]: 
    #     r["meta"].update({p: byc["beacon_info"][ snake_to_camel(p) ]})

    # if "biosamples" in byc["response_type"]:
    #     results = byc["dataset_responses"][0][ byc["dataset_ids"][0] ]
    #     populate_service_response(r, results)
    #     cgi_print_json_response( byc["form_data"], r, 200 )

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
