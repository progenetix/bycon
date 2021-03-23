#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path, environ, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )
sys.path.append( pkg_path )
from bycon.lib import *

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import *

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

    r["response"]["info"].update({
        "variant_count": len(vs),
        "biosample_count": byc["query_results"]["bs.id"][ "target_count" ]
    })

    ############################################################################

    if "pgxseg" in byc["method"]:
        export_pgxseg_download(ds_id, r, vs, byc)

    if "callsetsvariants" in byc["method"]:
        export_variants_download(vs, r, byc)

    ############################################################################

    query_results_save_handovers(byc)
    populate_service_response(r, vs)
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
