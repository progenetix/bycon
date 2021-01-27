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
from lib.service_utils import *

"""podmd
* <https://progenetix.org/services/variants/?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    variants("variants")
    
################################################################################

def variants(service):

    byc = initialize_service(service)

    select_dataset_ids(byc)
    beacon_check_dataset_ids(byc)
    get_filter_flags(byc)
    parse_filters(byc)

    parse_variants(byc)
    get_variant_request_type(byc)
    generate_queries(byc)

    r = create_empty_service_response(byc)

    # TODO: move somewhere
    if not byc[ "queries" ].keys():
      response_add_error(r, "No (correct) query parameters were provided." )
    if len(byc[ "dataset_ids" ]) < 1:
      response_add_error(r, "No `datasetIds` parameter provided." )
    if len(byc[ "dataset_ids" ]) > 1:
      response_add_error(r, "More than 1 `datasetIds` value was provided." )
    cgi_break_on_errors(r, byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(r, "dataset", ds_id )

    execute_bycon_queries( ds_id, byc )
    query_results_save_handovers(byc)

    access_id = byc["query_results"]["vs._id"][ "id" ]

    # # TODO: 
    # if "callsetstats" in byc["method"]:
    #     service = "callsets"
    #     access_id = byc["query_results"]["cs._id"][ "id" ]

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        response_add_error(r, e)

    cgi_break_on_errors(r, byc)

    results = [ ]

    for v in h_o_d:
        s = { }
        for k in byc["these_prefs"]["methods"][ byc["method"] ]:
            # TODO: harmless hack
            if "." in k:
                k1, k2 = k.split('.')
                s[ k ] = v[ k1 ][ k2 ]
            elif k in v.keys():
                if "start" in k or "end" in k:
                    s[ k ] = int(v[ k ])
                else:
                    s[ k ] = v[ k ]
            # else:
            #     s[ k ] = None
        results.append( s )

    populate_service_response(r, results)
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
