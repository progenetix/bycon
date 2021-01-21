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

    # adding arguments for querying / processing data
    parse_variants(byc)
    get_variant_request_type(byc)
    generate_queries(byc)

    # response prototype
    r = byc[ "config" ]["response_object_schema"]
    r.update( { "errors": byc["errors"], "warnings": byc["warnings"] } )

    # TODO: move somewhere
    if not byc[ "queries" ].keys():
      r["errors"].append( "No (correct) query parameters were provided." )
    if len(byc[ "dataset_ids" ]) < 1:
      r["errors"].append( "No `datasetIds` parameter provided." )
    if len(byc[ "dataset_ids" ]) > 1:
      r["errors"].append( "More than 1 `datasetIds` value was provided." )
    if len(r["errors"]) > 0:
      cgi_print_json_response( byc["form_data"], r, 422 )

    ds_id = byc[ "dataset_ids" ][ 0 ]

    # saving the parameters to the response
    for p in ["method", "filters", "variant_pars"]:
        r["parameters"].update( { p: byc[ p ] } )
    r["parameters"].update( { "dataset": ds_id } )
    r["response_type"] = service

    if "phenopackets" in byc["method"]:
        byc.update( { "response_type": "return_individuals" } )

    execute_bycon_queries( ds_id, byc )
    query_results_save_handovers(byc)

    access_id = byc["query_results"]["bs._id"][ "id" ]

    # TODO: 
    if "callsetstats" in byc["method"]:
        service = "callsets"
        access_id = byc["query_results"]["cs._id"][ "id" ]

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        r["errors"].append( e )

    if len(r["errors"]) > 0:
      cgi_print_json_response( byc["form_data"], r, 422 )

    for b_s in h_o_d:
        s = { }
        for k in byc["these_prefs"]["methods"][ byc["method"] ]:
            # TODO: harmless hack
            if "." in k:
                k1, k2 = k.split('.')
                s[ k ] = b_s[ k1 ][ k2 ]
            elif k in b_s.keys():
                s[ k ] = b_s[ k ]
            else:
                s[ k ] = None
        r["data"].append( s )

    r[service+"_count"] = len(r["data"])
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
