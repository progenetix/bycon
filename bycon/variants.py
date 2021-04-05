#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path, environ, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )

bycon_lib_path = path.join( pkg_path, "bycon", "lib" )
sys.path.append( bycon_lib_path )

from cgi_utils import cgi_break_on_errors, cgi_print_json_response
from variant_responses import retrieve_variants
from handover_generation import query_results_save_handovers
from query_generation import initialize_beacon_queries
from query_execution import execute_bycon_queries

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import create_empty_service_response, initialize_service, populate_service_response, response_add_parameter, response_collect_errors, export_variants_download, export_pgxseg_download

byconeer_lib_path = path.join( pkg_path, "byconeer", "lib" )
sys.path.append( byconeer_lib_path )

from schemas_parser import parse_beacon_schema

################################################################################
################################################################################
################################################################################

"""
https://progenetix.test/beacon/variants/?datasetIds=progenetix&filters=NCIT:C7712&method=pgxseg&debug=1
"""

def main():

    variants()
    
################################################################################

def variants():

    byc = initialize_service()

    parse_beacon_schema(byc)

    initialize_beacon_queries(byc)

    r = create_empty_service_response(byc)
    response_collect_errors(r, byc)
    cgi_break_on_errors(r, byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(r, "dataset", ds_id )
    execute_bycon_queries( ds_id, byc )

    ############################################################################

    vs = retrieve_variants(ds_id, r, byc)

    ############################################################################

    if "callsetspgxseg" in byc["method"]:
        export_pgxseg_download(ds_id, r, vs, byc)

    if "callsetsvariants" in byc["method"]:
        export_variants_download(vs, r, byc)

    ############################################################################

    query_results_save_handovers(byc)

    if "pgxseg" in byc["method"]:
        export_pgxseg_download(ds_id, r, vs, byc)

    populate_service_response( byc, r, vs)
    cgi_print_json_response( byc, r, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
