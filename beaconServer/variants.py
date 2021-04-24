#!/usr/local/bin/python3

import cgi, cgitb, sys
from os import path, environ, pardir

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

################################################################################
################################################################################
################################################################################

"""
https://progenetix.test/beacon/variants/?filters=NCIT:C7712&method=pgxseg&debug=1
"""

def main():

    variants()
    
################################################################################

def variants():

    byc = initialize_service()
    parse_beacon_schema(byc)

    initialize_beacon_queries(byc)

    create_empty_service_response(byc)
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(byc, "dataset", ds_id )
    execute_bycon_queries( ds_id, byc )

    ############################################################################

    h_o, e = handover_retrieve_from_query_results(byc)
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        response_add_error(byc, 422, e )

    # vs = retrieve_variants(ds_id, byc)

    populate_service_response( byc, h_o_d)
    
    ############################################################################

    # TODO: unify ...

    if "callsetspgxseg" in byc["method"]:
        export_pgxseg_download(ds_id, h_o_d, byc)

    if "callsetsvariants" in byc["method"]:
        export_variants_download(h_o_d, byc)

    if "pgxseg" in byc["method"]:
        export_pgxseg_download(ds_id, h_o_d, byc)

    ############################################################################

    query_results_save_handovers(byc)
    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
