#!/usr/local/bin/python3

import cgi, cgitb, sys
from os import path, environ, pardir

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from bycon import *

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

    create_empty_service_response(byc)
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(byc, "dataset", ds_id )
    execute_bycon_queries( ds_id, byc )

    ############################################################################

    vs = retrieve_variants(ds_id, byc)

    populate_service_response( byc, vs)
    
    ############################################################################

    if "callsetspgxseg" in byc["method"]:
        export_pgxseg_download(ds_id, vs, byc)

    if "callsetsvariants" in byc["method"]:
        export_variants_download(vs, byc)

    if "pgxseg" in byc["method"]:
        export_pgxseg_download(ds_id, vs, byc)

    ############################################################################

    query_results_save_handovers(byc)
    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
