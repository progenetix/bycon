import re, yaml
import json
from pymongo import MongoClient
from os import path as path
from os import environ

from .cgi_utils import *
from .beacon_process_handovers import *

################################################################################

def select_response_type(**byc):

    response_type = "respond_empty_request"
    if "response" in byc["endpoint_pars"]:
        if byc["endpoint_pars"]["response"]:
            response_type = "return_"+byc["endpoint_pars"]["response"]

    return response_type

################################################################################

def respond_empty_request(**byc):

    if not environ.get('REQUEST_URI'):
        return()
    if len(byc["form_data"]) > 0:
        return()
    if byc["endpoint"]:
        if not byc["endpoint"] == "/":
            return()
    if byc["args"]:
        if not byc["args"].info:
            return()

    # current default response
    cgi_print_json_response( byc["service_info"] )

################################################################################

def respond_get_datasetids_request(**byc):

    if not environ.get('REQUEST_URI'):
        return()

    if not "get-datasetids" in environ.get('REQUEST_URI'):
        return()

    dataset_ids = [ ]
    for ds_id in byc["datasets_info"].keys():
        dataset_ids.append( { "id": ds_id, "name": byc["datasets_info"][ds_id]["name"] } )
    cgi_print_json_response( { "datasets": dataset_ids } )

################################################################################

def respond_service_info_request(**byc):

    if not environ.get('REQUEST_URI'):
        return()

    if not "service-info" in environ.get('REQUEST_URI'):
        return()

    cgi_print_json_response( byc["service_info"] )

################################################################################

def respond_filtering_terms_request(**byc):

    if not "filtering_terms" in byc["endpoint"]:
        return()

    ks = [ "id", "name", "apiVersion" ]
    fks = [ "id", "label", "source" ]

    resp = { }
    for k in ks:
        if k in byc["service_info"]:
            resp.update( { k: byc["service_info"][ k ] } )

    fts = { }

    # for the general filter response, filters from *all* datasets are
    # being provided
    # if only one => counts are added back
    dss = byc["dbstats"]["datasets"].keys()
    if len(byc[ "dataset_ids" ]) == 1:
        ds_id = byc[ "dataset_ids" ][0]
        if ds_id in byc["dbstats"]["datasets"]:
            dss = [ ds_id ]
            fks.append("count")
            resp.update( { "datasetId": ds_id } )

    for ds_id in dss:
        ds = byc["dbstats"]["datasets"][ ds_id ]
        if "filtering_terms" in ds:
            for f in ds["filtering_terms"]:
                fts[f[ "id" ]] = {  }
                for l in fks:
                    fts[f[ "id" ]][ l ] = f[ l ]
 
    ftl = [ ]
    for key in sorted(fts):
        if len(byc["filters"]) > 0:
            for f in byc["filters"]:
                f_t = re.compile(r'^'+f)
                if f_t.match(key):
                    ftl.append( fts[key] )
        else: 
            ftl.append( fts[key] )

    resp.update( { "filteringTerms": ftl } )
    cgi_print_json_response(resp)

################################################################################

def create_dataset_response(ds_id, **byc):

    # TODO: getting the correct response structure from the schema

    dataset_allele_resp = {
        "datasetId": ds_id,
        "exists": False,
        "error": None,
        "variantCount": 0,
        "callCount": 0,
        "sampleCount": byc[ "query_results" ][ "bs._id" ][ "target_count" ],
        "frequency": 0,
        "note": "",
        "externalUrl": "",
        "info": { },
        "datasetHandover": [ ] }

    # TODO: The "true" may actually be fulfilled by non-variant query types in v2.
    if "vs._id" in byc[ "query_results" ]:
        dataset_allele_resp.update( {
            "variantCount": byc[ "query_results" ][ "vs.digest" ][ "target_count" ],
            "callCount": byc[ "query_results" ][ "vs._id" ][ "target_count" ]
        } )
        if dataset_allele_resp[ "variantCount" ] > 0:
            dataset_allele_resp.update( {
                "frequency": float("%.6f" % (dataset_allele_resp[ "callCount" ] / byc[ "dbstats" ]["datasets"][ds_id][ "counts" ][ "variants_distinct" ] ) )
            } )
            dataset_allele_resp[ "info" ].update( { "variants": byc[ "query_results" ][ "vs.digest" ][ "target_values" ] })

    for this_c in [ "variantCount", "callCount", "sampleCount" ]:
        if this_c in dataset_allele_resp:
            if dataset_allele_resp[ this_c ] > 0:
                 dataset_allele_resp.update( { "exists": True } )

    dataset_allele_resp.update( { "datasetHandover": dataset_response_add_handovers( ds_id, **byc ) } )

    return dataset_allele_resp

################################################################################

def create_beacon_response(**byc):

    # with open( path.join(path.abspath(byc[ "config" ][ "paths" ][ "module_root" ]), "config", "beacon_info.yaml") ) as bc:
    #     b_defs = yaml.load( bc , Loader=yaml.FullLoader)
    # print(b_defs)

    # TODO: getting the correct response structure from the schema

    b_response = {}

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
    b_response = {
        "exists": False,
        "beaconAlleleRequest" : byc[ "variant_pars" ]
    }

    for b_a in b_attr:
        try:
            b_response[ b_a ] = byc[ "service_info" ][ b_a ]
        except Exception:
            pass
 
    b_response[ "datasetAlleleResponses" ] = byc[ "dataset_responses" ]

    for b_r in b_response[ "datasetAlleleResponses" ]:
        if b_r[ "exists" ] == True:
            b_response[ "exists" ] = True

    return b_response

################################################################################

def callsets_return_stats(**byc):

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ byc[ "dataset_id" ] ]
    mongo_coll = mongo_db[ 'callsets' ]

    cs_stats = { }
    cs_stats["dup_fs"] = []
    cs_stats["del_fs"] = []
    cs_stats["cnv_fs"] = []

    for cs in mongo_coll.find({"_id": {"$in": byc["cs._id"] }}) :
        if "cnvstatistics" in cs["info"]:
            if "dupfraction" in cs["info"]["cnvstatistics"] and "delfraction" in cs["info"]["cnvstatistics"]:
                cs_stats["dup_fs"].append(cs["info"]["cnvstatistics"]["dupfraction"])
                cs_stats["del_fs"].append(cs["info"]["cnvstatistics"]["delfraction"])
                cs_stats["cnv_fs"].append(cs["info"]["cnvstatistics"]["cnvfraction"])

    mongo_client.close()

    return cs_stats

################################################################################
