#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path, environ, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from bycon.lib import *
from lib import *

"""podmd
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    beacon()
    
################################################################################

def beacon():

    byc = initialize_service("beacon")

    update_datasets_from_dbstats(byc)

    beacon_get_endpoint(byc)
    parse_endpoints(byc)
    select_response_type(byc)
    select_dataset_ids(byc)
    check_dataset_ids(byc)

    get_filter_flags(byc)
    parse_filters(byc)

    check_service_requests(byc)

    parse_variants(byc)
    get_variant_request_type(byc)
    
    generate_queries(byc)

    beacon_respond_with_errors(byc)

    r = create_empty_service_response(byc)
    response_collect_errors(r, byc)
    cgi_break_on_errors(r, byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(r, "dataset", ds_id )

    execute_bycon_queries( ds_id, byc )
    query_results_save_handovers(byc)

    # TODO: Beacon stats, dataset responses ...
    access_id = byc["query_results"]["bs._id"][ "id" ]
    if "variants" in byc["response_type"]:
        if "vs._id" in byc["query_results"]:
            access_id = byc["query_results"]["vs._id"][ "id" ]
        else:
            response_add_error(r, 422, "No variants were retrieved." )
 
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
