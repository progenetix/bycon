#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import environ, path, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib import *
from lib.service_utils import *

"""podmd
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    phenopackets("phenopackets")
    
################################################################################

def phenopackets(service):

    byc = initialize_service(service)

    for d in [
        "dataset_definitions",
        "filter_definitions",
        "geoloc_definitions",
        "variant_definitions",
        "handover_definitions"
    ]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

    for p_k, p_v in byc["these_prefs"]["parameters"].items():
        if p_k in byc["form_data"]:
            if "array" in p_v[ "type" ]:
                byc.update( { p_k: byc["form_data"].getlist( p_k ) } )
            else:
                byc.update( { p_k: byc["form_data"].getvalue( p_k ) } )

    byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
    byc.update( { "dataset_ids": beacon_check_dataset_ids( **byc ) } )
    byc.update( { "filter_flags": get_filter_flags( **byc ) } )
    byc.update( { "filters": parse_filters( **byc ) } )

    # adding arguments for querying / processing data
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    byc.update( { "queries": generate_queries( **byc ) } )

    # response prototype
    r = byc[ "config" ]["response_object_schema"]
    r.update( { "errors": byc["errors"], "warnings": byc["warnings"] } )

    # TODO: move somewhere
    if not byc[ "queries" ].keys():
      r["errors"].append( "No (correct) query parameters were provided." )
    if len(byc[ "dataset_ids" ]) < 1:
      r["errors"].append( "No `datasetIds` parameter provided." )
    if len(byc[ "dataset_ids" ]) > 1:
      r["errors"].append( "More than 1 `datasetIds` value were provided." )
    if len(r["errors"]) > 0:
      cgi_print_json_response( byc["form_data"], r, 422 )

    ds_id = byc[ "dataset_ids" ][ 0 ]

    # saving the parameters to the response
    for p in ["filters", "variant_pars"]:
        r["parameters"].update( { p: byc[ p ] } )
    r["parameters"].update( { "dataset": ds_id } )
    r["response_type"] = service

    byc.update( { "query_results": execute_bycon_queries( ds_id, **byc ) } )
    query_results_save_handovers( **byc )

    access_id = byc["query_results"]["bs._id"][ "id" ]

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        r["errors"].append( e )

    access_id_ind = byc["query_results"]["is._id"][ "id" ]
    ind_s = [ ]
    h_o_ind, e_ind = retrieve_handover( access_id_ind, **byc )
    h_o_d_ind, e_ind = handover_return_data( h_o_ind, e_ind )

    var_data = [ ]
    access_id_var = [ ]

    if "variantsaccessid" in byc["form_data"]:
        access_id_var = byc["form_data"].getvalue("variantsaccessid")
    elif "vs._id" in byc["query_results"]:
        access_id_var = byc["query_results"]["vs._id"]["id"]
    if len(access_id_var) > 1:
        h_o_var, e_var = retrieve_handover( access_id_var, **byc )
        var_data, e_var = handover_return_data( h_o_var, e_var )

    for i_s in h_o_d_ind:

        pxf = {
            "id": "pxf__"+i_s["id"],
            "subject": i_s["id"],
            "biosamples": [ ]
        }

        # TODO: method here retrieves & reformats the biosamples
        pxf_bs = list(filter(lambda d: d["individual_id"] == i_s["id"], h_o_d))
        for bs in pxf_bs:
            p_bs = {
                "id": bs["id"],
                "externalReferences": [ ],
            }
            if "histological_diagnosis" in bs:
                p_bs.update( { "histologicalDiagnosis": bs["histological_diagnosis"]})
            if "sampledTissue" in bs:
                p_bs.update( { "sampledTissue": bs["sampledTissue"]})
            if "external_references" in bs:
                p_bs.update( { "externalReferences": bs["external_references"]})

            # TODO: The `digest` here is just a minimal drop-in representation.
            # HGVS cannot be used since it doesn't allow DUP ...
            if len(var_data) > 0:
                bs_vars = list(filter( lambda x : x['biosample_id'] == bs["id"], var_data ) )
                if "progenetix" in byc["variant_format"]:
                    p_bs.update( { "variants": bs_vars } )
                else:
                    p_bs.update( { "variants": [ ] } )
                    for v in bs_vars:
                        if "digest" in byc["variant_format"]:
                            p_bs["variants"].append( v["digest"] )

            pxf["biosamples"].append( p_bs )

        r["data"].append( pxf )

    r["response_type"] = service

    if len(r["errors"]) > 0:
      cgi_print_json_response( byc["form_data"], r, 422 )

    r[service+"_count"] = len(r["data"])
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
