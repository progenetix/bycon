#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path, environ, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

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

from service_utils import initialize_service, create_empty_service_response,  response_collect_errors, response_add_parameter, populate_service_response, response_map_results

from byconeer.lib.schemas_parser import *

"""podmd
* <https://progenetix.org/cgi/bycon/services/biosamples.py?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.org/services/biosamples?responseFormat=simple&datasetIds=progenetix&filters=cellosaurus:CVCL_0030>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    biosamples()
    
################################################################################

def biosamples():

    byc = initialize_service()
    parse_beacon_schema(byc)

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    get_filter_flags(byc)
    parse_filters(byc)

    # adding arguments for querying / processing data
    parse_variants(byc)
    get_variant_request_type(byc)
    generate_queries(byc)

    r = create_empty_service_response(byc)
    response_collect_errors(r, byc)
    cgi_break_on_errors(r, byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(r, "dataset", ds_id )

    execute_bycon_queries( ds_id, byc )
    query_results_save_handovers(byc)

    # if "vs._id" in byc["query_results"]:
    #     print(byc["query_results"]["vs._id"][ "target_count" ])

    access_id = byc["query_results"]["bs._id"][ "id" ]

    # TODO: 
    if "callsetstats" in byc["method"]:
        access_id = byc["query_results"]["cs._id"][ "id" ]

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        response_add_error(r, 422, e )

    cgi_break_on_errors(r, byc)

    populate_service_response(r, response_map_results(h_o_d, byc))
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
