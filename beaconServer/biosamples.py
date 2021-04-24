#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path, environ, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd
* <https://progenetix.org/cgi/bycon/services/biosamples.py?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.org/beacon/biosamples?datasetIds=progenetix&filters=cellosaurus:CVCL_0030>
* <https://progenetix.org/beacon/biosamples/pgxbs-kftva5c8/variants/>
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

    cgi_break_on_errors(byc)

    populate_service_response( byc, h_o_d)
    # populate_service_response( byc, response_map_results(h_o_d, byc))

    query_results_save_handovers(byc)
    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
