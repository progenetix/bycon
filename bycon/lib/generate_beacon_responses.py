import re, yaml
import json
from pymongo import MongoClient
from os import environ

from cgi_utils import *
from handover_execution import *
from handover_generation import *
from query_execution import execute_bycon_queries

################################################################################

def check_service_requests(byc):

    respond_service_info_request(byc)
    respond_empty_request(byc)

################################################################################

def select_response_type(byc):

    byc.update( { "response_type": "respond_empty_request" } )
    if "response" in byc["endpoint_pars"]:
        if byc["endpoint_pars"]["response"]:
            byc.update( { "response_type": "return_"+byc["endpoint_pars"]["response"] } )

    return byc

################################################################################

def beacon_respond_with_errors( byc ):

    if not byc[ "queries" ].keys():
      byc["service_info"].update( { "error": { "error_code": 422, "error_message": "No (correct) query parameters were provided." } } )
      cgi_print_json_response( byc, byc["service_info"], 422)

    if len(byc[ "dataset_ids" ]) < 1:
      byc["service_info"].update( { "error": { "error_code": 422, "error_message": "No `datasetIds` parameter provided." } } )
      cgi_print_json_response( byc, byc["service_info"], 422)

################################################################################

def respond_empty_request( byc ):

    if not environ.get('REQUEST_URI'):
        return()
    if len(byc["form_data"]) > 0:
        return()
    if "endpoint" in byc:
        if not byc["endpoint"] == "/":
            return()
    if "args" in byc:
        if not byc["args"].info:
            return()

    # current default response
    cgi_print_json_response( byc, byc["service_info"], 200 )

################################################################################

def respond_service_info_request( byc ):

    if not environ.get('REQUEST_URI'):
        return()

    if not "service-info" in environ.get('REQUEST_URI'):
        return()

    cgi_print_json_response( byc, byc["service_info"], 200 )

################################################################################

def return_filtering_terms( byc ):

    fts = { }

    # for the general filter response, filters from *all* datasets are
    # provided
    # if only one => counts are added back

    for ds in byc[ "beacon_info" ][ "datasets" ]:
        if len(byc[ "dataset_ids" ]) > 0:
            if not ds["id"] in byc[ "dataset_ids" ]:
                continue
        if "filtering_terms" in ds:
            for f_t in ds[ "filtering_terms" ]:
                f_id = f_t[ "id" ]
                if not f_id in fts:
                    fts[ f_id ] = f_t
                else:
                    fts[ f_id ][ "count" ] += f_t[ "count" ]
  
    ftl = [ ]
    for key in sorted(fts):
        f_t = fts[key]
        if len(byc[ "dataset_ids" ]) > 1:
            del(f_t["count"])
        if "filters" in byc:
            if len(byc["filters"]) > 0:
                for f in byc["filters"]:
                    f_t = re.compile(r'^'+f)
                    if f_t.match(key):
                        ftl.append( f_t )
        else: 
            ftl.append( f_t )

    return ftl

################################################################################

def collect_dataset_responses(byc):

    byc.update( { "dataset_responses": [ ] } )

    for ds_id in byc[ "dataset_ids" ]:

        execute_bycon_queries( ds_id, byc )
        query_results_save_handovers(byc)

        if byc["response_type"] == "return_biosamples":
            access_id = byc["query_results"]["biosamples._id"][ "id" ]
        elif byc["response_type"] == "return_variants":
            access_id = byc["query_results"]["variants._id"][ "id" ]
        else:
            byc["dataset_responses"].append( create_dataset_response( ds_id, byc ) )
            continue

        h_o, e = retrieve_handover( access_id, **byc )
        h_o_d, e = handover_return_data( h_o, e )
        byc["dataset_responses"].append( { ds_id: h_o_d } )

    return byc

################################################################################

def create_dataset_response(ds_id, byc):

    # TODO: getting the correct response structure from the schema

    dataset_allele_resp = {
        "datasetId": ds_id,
        "exists": False,
        "error": None,
        "variantCount": 0,
        "callCount": 0,
        "sampleCount": byc[ "query_results" ][ "biosamples._id" ][ "target_count" ],
        "frequency": 0,
        "note": "",
        "externalUrl": "",
        "info": { },
        "datasetHandover": [ ] }

    # TODO: The "true" may actually be fulfilled by non-variant query types in v2.
    if "variants._id" in byc[ "query_results" ]:
        dataset_allele_resp.update( {
            "variantCount": byc[ "query_results" ][ "variants.digest" ][ "target_count" ],
            "callCount": byc[ "query_results" ][ "variants._id" ][ "target_count" ]
        } )
        if dataset_allele_resp[ "variantCount" ] > 0:
            for b_i_ds in byc[ "beacon_info" ]["datasets"]:
                if ds_id == b_i_ds["id"]:
                    dataset_allele_resp.update({
                        "frequency": float("%.6f" % (dataset_allele_resp[ "callCount" ] / b_i_ds[ "callCount"] ) )
                        } )
            dataset_allele_resp[ "info" ].update( { "variants": byc[ "query_results" ][ "variants.digest" ][ "target_values" ] })

    for this_c in [ "variantCount", "callCount", "sampleCount" ]:
        if this_c in dataset_allele_resp:
            if dataset_allele_resp[ this_c ] > 0:
                 dataset_allele_resp.update( { "exists": True } )

    dataset_allele_resp.update( { "datasetHandover": dataset_response_add_handovers( ds_id, **byc ) } )

    return dataset_allele_resp

################################################################################

def create_beacon_response(byc):

    # TODO: getting the correct response structure from the schema

    b_response = { "exists": False, "resultsHandover": [ ] }
    b_meta = { "receivedRequest": { "query": byc[ "variant_pars" ] } }

    if byc["response_type"] == "return_biosamples":
        b_response = { "biosamples": { } }
        for dsr in byc[ "dataset_responses" ]:
            for k in dsr.keys():
                b_response["biosamples"][k] = dsr[k]
        return b_response
    elif byc["response_type"] == "return_variants":
        b_response = { "g_variants": { } }
        for dsr in byc[ "dataset_responses" ]:
            for k in dsr.keys():
                b_response["g_variants"][k] = dsr[k]
        return b_response

    b_attr = [ "id", "beaconId", "name", "serviceUrl", 'organization', 'apiVersion', "info", "updateDateTime" ]

    for b_a in b_attr:
        try:
            b_meta[ b_a ] = byc[ "service_info" ][ b_a ]
        except Exception:
            pass
 
    b_response[ "datasetAlleleResponses" ] = byc[ "dataset_responses" ]

    for b_r in b_response[ "datasetAlleleResponses" ]:
        if b_r[ "exists" ] == True:
            b_response[ "exists" ] = True

    byc.update( { "service_response":{ "meta": b_meta, "response": { "datasetAlleleResponses": byc[ "dataset_responses" ] } } } )

    return byc

################################################################################
