#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import environ, path, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from beaconServer.lib import *
from beaconServer.lib.service_utils import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    phenopackets()
    
################################################################################

def phenopackets():

    byc = initialize_service()

    for p_k, p_v in byc["these_prefs"]["parameters"].items():
        # TODO: parameter checks ...
        if p_k in byc["form_data"]:
            byc.update( { p_k: byc["form_data"][p_k] } )

    select_dataset_ids(byc)
    check_dataset_ids(byc)
    get_filter_flags(byc)
    parse_filters(byc)

    parse_variants(byc)
    get_variant_request_type(byc)
    generate_queries(byc)

    create_empty_service_response(byc)    
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(byc, "dataset", ds_id )
    
    execute_bycon_queries( ds_id, byc )
    query_results_save_handovers(byc)

    ds_results = byc["dataset_results"][ds_id]

    access_id = ds_results["biosamples._id"][ "id" ]

    h_o, e = retrieve_handover( access_id, byc )
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        response_add_error(byc, 422, e )

    access_id_ind = ds_results["individuals._id"][ "id" ]
    ind_s = [ ]
    h_o_ind, e_ind = retrieve_handover( access_id_ind, byc )
    h_o_d_ind, e_ind = handover_return_data( h_o_ind, e_ind )

    var_data = [ ]
    access_id_var = [ ]

    if "variantsaccessid" in byc["form_data"]:
        access_id_var = byc["form_data"]["variantsaccessid"]
    elif "variants._id" in ds_results:
        access_id_var = ds_results["variants._id"]["id"]
    if len(access_id_var) > 1:
        h_o_var, e_var = retrieve_handover( access_id_var, byc )
        var_data, e_var = handover_return_data( h_o_var, e_var )

    results = [ ]

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

        results.append( pxf )

    populate_service_response( byc, results)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
