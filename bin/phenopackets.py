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
from bycon.read_specs import *

"""podmd
* <https://progenetix.org/cgi/bycon/bin/phenopackets.py?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus&debug=1>
* https://progenetix.org/services/phenopackets?do=phenopackets&accessid=b6340d0f-1c55-42fc-9372-0f7a4f4f5581&variantsaccessid=20b15bd5-2acf-4f36-b143-c1dc24f5191f&debug=1
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    phenopackets("phenopackets")
    
################################################################################

def phenopackets(service):

    config = read_bycon_config( path.abspath( dir_path ) )
    these_prefs = read_named_prefs( service, dir_path )

    byc = {
        "config": config,
        "form_data": cgi_parse_query(),
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "variant_defs": read_named_prefs( "variant_definitions", dir_path ),
        "h->o": read_named_prefs( "beacon_handovers", dir_path ),
        "errors": [ ],
        "warnings": [ ],
        "datasets_info": read_yaml_with_key_to_object( "beacon_datasets_file", "datasets", **config[ "paths" ] )
    }

    # first pre-population w/ defaults
    for p_k, p_v in these_prefs["parameters"].items():
        if "default" in p_v:
            byc.update( { p_k: p_v[ "default" ] } )
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
    byc.update( { "queries": create_queries( **byc ) } )

    # response prototype
    r = config["response_object_schema"]
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
                "histologicalDiagnosis": "",
                "externalReferences": [ ],
            }
            ncit = list(filter(lambda d: "NCIT" in d["type"]["id"], bs["biocharacteristics"]))
            if ncit:
                p_bs.update( { "histologicalDiagnosis": ncit[0]["type"] })
            if "sampledTissue" in bs:
                p_bs.update( { "sampledTissue": bs["sampledTissue"]})
            if "external_references" in bs:
                for e_r in bs["external_references"]:
                    p_bs["externalReferences"].append(e_r["type"])

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
