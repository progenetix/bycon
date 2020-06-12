import re, yaml
import json
from pymongo import MongoClient
from os import path as path
from os import environ

from .cgi_utils import *

################################################################################

def respond_empty_request(**byc):

    if not environ.get('REQUEST_URI'):
        return()
    if len(byc["rest_pars"]) > 0:
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

    # TODO: in its own module
    if not environ.get('REQUEST_URI'):
        return()

    if not "filtering_terms" in environ.get('REQUEST_URI'):
        return()
    
    rest_pars = cgi_parse_path_params( "filtering_terms" )

    filters =  [ ]
    pres = [ ]
    if "filters" in rest_pars:
        pres = rest_pars["filters"].split(",")

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
    if "datasetId" in rest_pars:
        if rest_pars["datasetId"] in byc["dbstats"]["datasets"]:
            dss = [ rest_pars["datasetId"] ]
            fks.append("count")
            resp.update( { "datasetId": rest_pars["datasetId"] } )

    for ds_id in dss:
        ds = byc["dbstats"]["datasets"][ ds_id ]
        if "filtering_terms" in ds:
            for f in ds["filtering_terms"]:
                fts[f[ "id" ]] = {  }
                for l in fks:
                    fts[f[ "id" ]][ l ] = f[ l ]
 
    ftl = [ ]
    for key in sorted(fts):
        if len(pres) > 0:
            for f in pres:
                f_t = re.compile(r'^'+f)
                if f_t.match(key):
                    ftl.append( fts[key] )
        else: 
            ftl.append( fts[key] )

    resp.update( { "filteringTerms": ftl } )
    cgi_print_json_response(resp)

################################################################################

def create_dataset_response(**byc):

    # TODO: getting the correct response structure from the schema

    dataset_allele_resp = {
        "datasetId": byc[ "dataset_id" ],
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
                "frequency": float("%.6f" % (dataset_allele_resp[ "callCount" ] / byc[ "dbstats" ]["datasets"][ byc[ "dataset_id" ] ][ "counts" ][ "variants_distinct" ] ) )
            } )
            dataset_allele_resp[ "info" ].update( { "variants": byc[ "query_results" ][ "vs.digest" ][ "target_values" ] })

    for this_c in [ "variantCount", "callCount", "sampleCount" ]:
        if this_c in dataset_allele_resp:
            if dataset_allele_resp[ this_c ] > 0:
                 dataset_allele_resp.update( { "exists": True } )

    dataset_allele_resp.update( { "datasetHandover": _dataset_response_add_handovers(**byc) } )

    return( dataset_allele_resp )

################################################################################

def _dataset_response_add_handovers(**byc):

    b_h_o = [ ]

    ds_h_o =  byc["datasets_info"][ byc[ "dataset_id" ] ]["handoverTypes"]
    h_o_types = byc["h->o"]["h->o_types"]

    ho_client = MongoClient()
    ho_db = ho_client[ byc["config"]["info_db"] ]
    ho_coll = ho_db[ byc["config"][ "handover_coll" ] ]

    h_o_db_k = [ ]

    for h_o_t in h_o_types.keys():

        h_o_defs = h_o_types[ h_o_t ]

        if not h_o_t in ds_h_o:
            continue

        for h_o_key in byc[ "query_results" ].keys():
            h_o = byc[ "query_results" ][ h_o_key ]
            if h_o_key == h_o_types[ h_o_t ][ "h->o_key" ]:
                if not h_o_key in h_o_db_k:
                    h_o_db_k.append(h_o)
                    ho_coll.update_one( { "id": h_o["id"] }, { '$set': h_o }, upsert=True )

                h_o_r = {
                    "handoverType": {
                        "id": h_o_defs[ "id" ],
                        "label": h_o_defs[ "label" ],
                    },
                    "description": h_o_defs[ "description" ],
                }

                www = str(environ.get('SERVER_NAME'))

                if "script_path_web" in h_o_defs:
                    if re.compile( ".test" ).match( www ):
                        h_o_defs["script_path_web"].replace( ".org", ".test")
                    h_o_r.update( { "url": "{}?do={}&accessid={}".format(h_o_defs["script_path_web"], h_o_t, h_o["id"]) } )

                b_h_o.append( h_o_r )

    return( b_h_o )

################################################################################

# def create_handover_exporter(**byc):









################################################################################

def create_beacon_response(**byc):

    # with open( path.join(path.abspath(byc[ "config" ][ "paths" ][ "module_root" ]), "config", "beacon_info.yaml") ) as bc:
    #     b_defs = yaml.load( bc , Loader=yaml.FullLoader)
    # print(b_defs)

    # TODO: getting the correct response structure from the schema

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

    return( b_response )

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
