#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path as path
from os import environ
import sys, os, datetime, argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""podmd
### Bycon - a Python-based environment for the Beacon v2 genomics API

Please see the [documentation](./doc/byconplus.md) for more information.

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-t", "--test", action='store_true', help="test from command line with default parameters")
    parser.add_argument("-i", "--info", action='store_true', help="test from command line for info")
    parser.add_argument("-n", "--filtering_terms", action='store_true', help="test filtering term response")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    byconplus()
    
################################################################################

def byconplus():
    
    config = read_bycon_config( path.abspath( dir_path ) )
    form_data = cgi_parse_query()
    args = _get_args()

    # TODO: "byc" becoming a proper object?!
    byc = {
        "config": config,
        "args": args,
        "form_data": form_data,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "variant_defs": read_variant_definitions( **config[ "paths" ] ),
        "datasets_info": read_datasets_info( **config[ "paths" ] ),
        "service_info": read_service_info( **config[ "paths" ] ),
        "beacon_info": read_beacon_info( **config[ "paths" ] ),
        "beacon_paths": read_beacon_api_paths( **config[ "paths" ] ),
        "h->o": read_handover_info( **config[ "paths" ] ),
        "dbstats": dbstats_return_latest( **config ),
        "get_filters": False
    }

    byc["beacon_info"].update( { "datasets": update_datasets_from_dbstats(**byc) } )
    for par in byc[ "beacon_info" ]:
        byc[ "service_info" ][ par ] = byc[ "beacon_info" ][ par ]

    byc.update( { "endpoint": beacon_get_endpoint(**byc) } )
    byc.update( { "endpoint_pars": parse_endpoints( **byc ) } )
    byc.update( { "response_type": select_response_type( **byc ) } )

    byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
    byc.update( { "filters":  parse_filters( **byc ) } )

    respond_filtering_terms_request(**byc)
    respond_service_info_request(**byc)
    respond_empty_request(**byc)
    respond_get_datasetids_request(**byc)

    # adding arguments for querying / processing data
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    # print(byc["variant_request_type"])
    byc.update( { "queries": beacon_create_queries( **byc ) } )
    # print(byc["queries"])

    # fallback - but maybe shouldbe an error response?
    if not byc[ "queries" ].keys():
        cgi_print_json_response(byc["service_info"])

    # TODO: There should be a better pplace for this ...
    if len(byc[ "dataset_ids" ]) < 1:
        cgi_exit_on_error("No `datasetIds` parameter provided.")

    # TODO: vove the response modification to somewhere sensible...
    dataset_responses = [ ]

    for ds_id in byc[ "dataset_ids" ]:

        byc.update( { "query_results": execute_bycon_queries( ds_id, **byc ) } )
        query_results_save_handovers( **byc )

        if byc["response_type"] == "return_biosamples":
            bios = handover_return_data( byc["query_results"]["bs._id"][ "id" ], **byc )
            dataset_responses.append( { ds_id: bios } )
        elif byc["response_type"] == "return_variants":
            vs = handover_return_data( byc["query_results"]["vs._id"][ "id" ], **byc )
            dataset_responses.append( { ds_id: vs } )
        else:
            dataset_responses.append( create_dataset_response( ds_id, **byc ) )   

    byc.update( { "dataset_responses": dataset_responses } )
    beacon_response = create_beacon_response(**byc)
    
    cgi_print_json_response(beacon_response)

################################################################################
################################################################################

if __name__ == '__main__':
    main()
