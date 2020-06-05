import re, yaml
import json
from pymongo import MongoClient
from os import path as path
from os import environ

from .cgi_utils import *
################################################################################

def read_service_info(**byc):

    ofp = path.join( byc[ "config" ][ "paths" ][ "module_root" ], *byc[ "config" ][ "paths" ][ "service_info_file" ] )
    with open(ofp) as of:
        s_info = yaml.load( of , Loader=yaml.FullLoader)
        return(s_info["service_info"])

################################################################################

def read_beacon_info(**byc):

    ofp = path.join( byc[ "config" ][ "paths" ][ "module_root" ], *byc[ "config" ][ "paths" ][ "beacon_info_file" ] )
    with open(ofp) as of:
        b_info = yaml.load( of , Loader=yaml.FullLoader)
        return(b_info["beacon_info"])

################################################################################

def read_datasets_info(**byc):

    ofp = path.join( byc[ "config" ][ "paths" ][ "module_root" ], *byc[ "config" ][ "paths" ][ "beacon_datasets_file" ] )
    with open(ofp) as of:
        ds = yaml.load( of , Loader=yaml.FullLoader)
        return(ds["datasets"])

################################################################################

def dbstats_return_latest(**byc):

# db.dbstats.find().sort({date:-1}).limit(1)
    dbstats_coll = MongoClient( )[ byc[ "config" ][ "info_db" ] ][ byc[ "config" ][ "beacon_info_coll" ] ]
    stats = dbstats_coll.find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( 1 )
    return(stats[0])

################################################################################

def update_datasets_from_db(**byc):

    ds_with_counts = [ ]
    for ds in byc["datasets_info"]:
        ds_id = ds["id"]
        if ds_id in byc["dbstats"]:
            for k, l in byc["config"]["beacon_info_count_labels"].items():
                if "counts" in byc["dbstats"][ ds_id ]:
                    if k in byc["dbstats"][ ds_id ]["counts"]:
                        ds[ l ] = byc["dbstats"][ ds_id ]["counts"][ k ]
            if "filtering_terms" in byc["dbstats"][ ds_id ]:
                ds[ "filtering_terms" ] = byc["dbstats"][ ds_id ][ "filtering_terms" ]
        ds_with_counts.append(ds)

    return(ds_with_counts)

################################################################################

def web_return_filtering_terms(**byc):

    # prototyping some info endpoints => to be factored out ...
    if not environ.get('REQUEST_URI'):
        return()

    if not "filtering_terms" in environ.get('REQUEST_URI'):
        return()
    
    rest_pars = cgi_parse_path_params( "filtering_terms" )
    
    pres =  [  ]
    if "prefixes" in rest_pars:
        pres = rest_pars["prefixes"].split(",")

    ks = ( "id", "name", "apiVersion" )
    resp = { }
    fts = { }
    # for the general filter response, filters from *all* datasets are
    # being provided
    for ds_id in byc["dbstats"]["datasets"].keys():
        ds = byc["dbstats"]["datasets"][ ds_id ]
        if "filtering_terms" in ds:
            for f in ds["filtering_terms"]:
                fts[f[ "id" ]] = {  }
                for l in ( "id", "label", "source" ):
                    fts[f[ "id" ]][ l ] = f[ l ]
    ftl = [ ]
    split_v = re.compile(r'^(\w+?)[\:\-](\w[\w\.]+?)$')
    for key in sorted(fts):
        if len(pres) > 0:
            if split_v.match(key):
                pre, code = split_v.match(key).group(1, 2)
                if pre in pres:
                    ftl.append( fts[key] )
        else: 
            ftl.append( fts[key] )

    for k in ks:
        if k in byc["service_info"]:
            resp.update( { k: byc["service_info"][ k ] } )

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
        "sampleCount": len( byc[ "query_results" ][ "biosamples::_id" ] ),
        "frequency": 0,
        "note": "",
        "externalUrl": "",
        "info": { },
        "datasetHandover": [ ] }

    # TODO: The "true" may actually be fulfilled by non-variant query types in v2.
    if "variants::_id" in byc[ "query_results" ]:
        dataset_allele_resp.update( {
            "variantCount": len( byc[ "query_results" ][ "variants::digest" ] ),
            "callCount": len( byc[ "query_results" ][ "variants::_id" ] )
        } )
        if dataset_allele_resp[ "variantCount" ] > 0:
            dataset_allele_resp.update( {
                "frequency": float("%.6f" % (dataset_allele_resp[ "callCount" ] / byc[ "dbstats" ][ byc[ "dataset_id" ] ][ "counts" ][ "variants_distinct" ] ) )
            } )
            dataset_allele_resp[ "info" ].update( { "variants": byc[ "query_results" ][ "variants::digest" ] })

    for this_c in [ "variantCount", "callCount", "sampleCount" ]:
        if this_c in dataset_allele_resp:
            if dataset_allele_resp[ this_c ] > 0:
                 dataset_allele_resp.update( { "exists": True } )

    return( dataset_allele_resp )

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
    # print( byc[ "service_info" ].keys() )
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

    for cs in mongo_coll.find({"_id": {"$in": byc["callsets::_id"] }}) :
        if "cnvstatistics" in cs["info"]:
            if "dupfraction" in cs["info"]["cnvstatistics"] and "delfraction" in cs["info"]["cnvstatistics"]:
                cs_stats["dup_fs"].append(cs["info"]["cnvstatistics"]["dupfraction"])
                cs_stats["del_fs"].append(cs["info"]["cnvstatistics"]["delfraction"])
                cs_stats["cnv_fs"].append(cs["info"]["cnvstatistics"]["cnvfraction"])

    mongo_client.close()

    return cs_stats

################################################################################
