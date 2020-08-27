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

podmd"""

################################################################################
################################################################################
################################################################################


def main():

    biosamples()
    
################################################################################

def biosamples():
    
    config = read_bycon_config( path.abspath( dir_path ) )
    these_prefs = read_yaml_to_object( "biosamples_preference_file", **config[ "paths" ] )

    byc = {
        "config": config,
        "form_data": cgi_parse_query(),
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "variant_defs": read_yaml_to_object( "variant_definitions_file", **config[ "paths" ] ),
        "h->o": read_yaml_to_object( "handover_types_file", **config[ "paths" ] ),
        "datasets_info": read_yaml_with_key_to_object( "beacon_datasets_file", "datasets", **config[ "paths" ] )
    }

    # first pre-population w/ defaults
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
    byc.update( { "dataset_ids": beacon_check_dataset_ids( **byc ) } )
    byc.update( { "filter_flags": get_filter_flags( **byc ) } )
    byc.update( { "filters": parse_filters( **byc ) } )

    # adding arguments for querying / processing data
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    byc.update( { "queries": beacon_create_queries( **byc ) } )

    # response prototype
    r = config["response_object_schema"]

    # saving the parameters to the response
    for p in ["dataset_ids", "method", "filters", "variant_pars"]:
        r["parameters"].update( { p: byc[ p ] } )
    r["data"]["biosamples"] = { }

    # TODO: move somewhere
    if not byc[ "queries" ].keys():
      r["errors"].append( "No (correct) query parameters were provided." )
    if len(byc[ "dataset_ids" ]) < 1:
      r["errors"].append( "No `datasetIds` parameter provided." )
    if len(r["errors"]) > 0:
      cgi_print_json_response( byc["form_data"], r )

    # TODO: shouldn't this be just for one dataset?
    for ds_id in byc[ "dataset_ids" ]:
        byc.update( { "query_results": execute_bycon_queries( ds_id, **byc ) } )
        query_results_save_handovers( **byc )
        access_id = byc["query_results"]["bs._id"][ "id" ]
        bio_s = [ ]
        h_o, e = retrieve_handover( access_id, **byc )
        h_o_d, e = handover_return_data( h_o, e )
        if e:
            r["errors"].append( e )
            continue
        for b_s in h_o_d:
            s = { }
            for k in these_prefs["methods"][ byc["method"] ]:
                # TODO: harmless hack
                if k in b_s.keys():
                    s[ k ] = b_s[ k ]
                else:
                    s[ k ] = None
            bio_s.append( s )
        r["data"]["biosamples"].update( { ds_id: bio_s } )

    # TODO: legacy hack here for simple list response; remove after adjusting progenetix-next
    if "do" in byc["form_data"]:
        do = byc["form_data"].getvalue("do")
        if "biosamplesdata" in do:
            cgi_print_json_response( byc["form_data"], r["data"]["biosamples"][ byc[ "dataset_ids" ][0] ] )

    cgi_print_json_response( byc["form_data"], r )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
