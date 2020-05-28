import re, yaml
import json
from pymongo import MongoClient
from os import path as path
from os import environ

################################################################################

def read_beacon_info(**byc):

    ofp = path.join( byc[ "config" ][ "paths" ][ "module_root" ], *byc[ "config" ][ "paths" ][ "beacon_info_file" ] )

    with open(ofp) as of:
        b_info = yaml.load( of , Loader=yaml.FullLoader)

    return(b_info)

################################################################################

def generate_beacon_info(**byc):

    with open( path.join(path.abspath(byc[ "config" ][ "paths" ][ "module_root" ]), "config", "beacon_info.yaml") ) as bc:
        b_defs = yaml.load( bc , Loader=yaml.FullLoader)
            
    service_info = b_defs[ "service_info" ]

    """podmd
    
    For compatibility with the GA4GH "Service Info" standard, a separate
    endpoint is activated when calling with the path parameter.
    
    Some of the values are then added/adjusted for the legacy Beacon info
    response.
    
    podmd"""
        
    for par in b_defs[ "beacon_info" ]:
        service_info[ par ] = b_defs[ "beacon_info" ][ par ]
        
    """podmd
    The counts for the collections (`variants`, `biosamples` etc.) of the
    different datasets are retrieved from the daily updated 
    `progenetix.dbstats` collection.

    For the non-parametrized call of the application, just the basic
    information including variant counts is returned.

    podmd"""

    ds_with_counts = [ ]
    for dataset in b_defs[ "beacon_info" ][ "datasets" ]:
        if dataset["id"] in byc[ "config" ][ "dataset_ids" ]:
            dataset[ "callCount" ] = byc[ "dbstats" ][ dataset["id"]+"__variants" ][ "count" ]
            dataset[ "variantCount" ] = byc[ "dbstats" ][ dataset["id"]+"__variants" ][ "distincts_count_digest" ]
            dataset[ "sampleCount" ] = byc[ "dbstats" ][ dataset["id"]+"__biosamples" ][ "count" ]

            if "get_filters" in byc:
                print("retrieving filters for {}".format(dataset["id"]))
                dataset[ "filtering_terms" ] = dataset_get_filters(dataset["id"], **byc)
                print("=> {} filters in {}".format(len( dataset[ "filtering_terms" ] ), dataset["id"]))

            ds_with_counts.append(dataset)
        
    service_info[ "datasets" ] = ds_with_counts
  
    return( service_info )


################################################################################

def dataset_get_filters(dataset_id, **byc):

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ dataset_id ]
    bios_coll = mongo_db[ 'biosamples' ]

    filter_v = [ ]
    biocs = bios_coll.distinct( "biocharacteristics.type.id" )

    split_v = re.compile(r'^(\w+?)[\:\-](\w[\w\.]+?)$')

    for b in biocs:

        if split_v.match(b):
            pre, code = split_v.match(b).group(1, 2)
        else:
            continue

        l = ""
        labs = bios_coll.find_one( { "biocharacteristics.type.id": b } )
        for bio_c in labs[ "biocharacteristics" ]:
            if re.match( b, bio_c[ "type" ][ "id" ] ):
                l = bio_c[ "type" ][ "label" ]
                continue
        f = {
            "source": byc[ "filter_defs" ][ pre ][ "name" ],
            "id": b,
            "label": l
        }
        filter_v.append( f )

    return(filter_v)

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
                "frequency": float("%.6f" % (dataset_allele_resp[ "callCount" ] / byc[ "dbstats" ][ byc[ "dataset_id" ]+"__variants" ][ "count" ] ) )
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

def dbstats_return_latest(**byc):

# db.dbstats.find().sort({date:-1}).limit(1)
    dbstats_coll = MongoClient( )[ byc[ "config" ][ "info_db" ] ][ byc[ "config" ][ "stats_collection" ] ]
    stats = dbstats_coll.find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( 1 )
    return(stats[0])

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
