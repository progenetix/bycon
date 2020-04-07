import re, yaml
import json
from pymongo import MongoClient
from os import path as path
from os import environ

################################################################################

def return_beacon_info(**kwargs):

    with open( path.join(path.abspath(kwargs[ "config" ][ "paths" ][ "module_root" ]), "config", "beacon_info.yaml") ) as bc:
        b_defs = yaml.load( bc , Loader=yaml.FullLoader)
            
    service_info = b_defs[ "service_info" ]

    """podmd
    
    For compatibility with the GA4GH "Service Info" standard, a separate
    endpoint is activated when calling with the path parameter.
    
    Some of the values are then added/adjusted for the legacy Beacon info
    response.
    
    podmd"""
    
    if environ.get("REQUEST_URI"):
        if "/service-info" in environ['REQUEST_URI']:
            print(json.dumps(service_info, indent=4, sort_keys=True, default=str))
            exit( )
    
    for par in b_defs[ "beacon_info" ]:
        service_info[ par ] = b_defs[ "beacon_info" ][ par ]
        
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ kwargs[ "config" ][ "info_db" ] ]
    mongo_coll = mongo_db[ 'dbstats' ]
    
    stats = mongo_coll.find_one( { }, sort=[( '_id', -1 )] )

    mongo_client.close( )   

    """podmd
    The counts for the collections (`variants`, `biosamples` etc.) of the
    different datasets are retrieved from the daily updated 
    `progenetix.dbstats` collection.

    For the non-parametrized call of the application, just the basic
    information including variant counts is returned.

    podmd"""

    ds_with_counts = [ ]
    for dataset in b_defs[ "beacon_info" ][ "datasets" ]:
        if dataset["id"] in kwargs[ "config" ][ "dataset_ids" ]:
            dataset[ "callCount" ] = stats[ dataset["id"]+"__variants" ][ "count" ]
            dataset[ "variantCount" ] = stats[ dataset["id"]+"__variants" ][ "distincts_count_digest" ]
            dataset[ "sampleCount" ] = stats[ dataset["id"]+"__biosamples" ][ "count" ]
            ds_with_counts.append(dataset)
        
    service_info[ "datasets" ] = ds_with_counts
  
    return( service_info )


################################################################################

def create_dataset_response(**kwargs):

    # TODO: getting the correct response structure from the schema

    dataset_allele_resp = {
        "datasetId": kwargs[ "dataset_id" ],
        "exists": False,
        "error": "",
        "variantCount": kwargs[ "query_results" ][ "counts" ][ "variants" ],
        "callCount": kwargs[ "query_results" ][ "counts" ][ "variants" ],
        "sampleCount": kwargs[ "query_results" ][ "counts" ][ "biosamples" ],
        "frequency": 0,
        "note": "",
        "externalUrl": "",
        "info": { },
        "datasetHandover": [ ] }

    # TODO: The "true" may actually be fulfilled by non-variant query types in v2.

    if dataset_allele_resp[ "variantCount" ] > 0:
        dataset_allele_resp[ "exists" ] = True
        dataset_allele_resp[ "info" ].update( { "variants": kwargs[ "query_results" ][ "variants::digest" ] })
    if dataset_allele_resp[ "variantCount" ] > 0:
        dataset_allele_resp[ "frequency" ] = float("%.5f" % (dataset_allele_resp[ "variantCount" ] / kwargs[ "query_results" ][ "counts" ][ "variants_all" ]) )


    return( dataset_allele_resp )

################################################################################

def create_beacon_response(**kwargs):

    # with open( path.join(path.abspath(kwargs[ "config" ][ "paths" ][ "module_root" ]), "config", "beacon_info.yaml") ) as bc:
    #     b_defs = yaml.load( bc , Loader=yaml.FullLoader)
    # print(b_defs)

    # TODO: getting the correct response structure from the schema

    b_attr = [ "id", "beaconId", "name", "serviceUrl", 'organization', 'apiVersion', "info", "updateDateTime" ]
    b_response = { "exists": False }
    # print( kwargs[ "service_info" ].keys() )
    for b_a in b_attr:
        try:
            b_response[ b_a ] = kwargs[ "service_info" ][ b_a ]
        except Exception:
            pass
 
    b_response[ "datasetAlleleResponses" ] = kwargs[ "dataset_responses" ]

    for b_r in b_response[ "datasetAlleleResponses" ]:
        if b_r[ "exists" ] == True:
            b_response[ "exists" ] = True

    return( b_response )


################################################################################


