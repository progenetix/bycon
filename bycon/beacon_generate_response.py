import re, yaml
import json
from pymongo import MongoClient
from os import path as path
from os import environ

################################################################################

def return_beacon_info(config, dir_path):

    with open( path.join(path.abspath(dir_path), "..", "config", "beacon_info.yaml") ) as bc:
        b_defs = yaml.load( bc , Loader=yaml.FullLoader)
            
    service_info = b_defs[ "service_info" ]

    """podmd
    
    For compatibility with the GA4GH "Service Info" standard, a separate
    endpoint is activated when calling with the path parameter.
    
    Some of the values are then added/adjusted for the legacy Beacon info
    response.
    
    end_podmd"""
    
    if "/service-info" in environ['REQUEST_URI']:
        print(json.dumps(service_info, indent=4, sort_keys=True, default=str))
        exit( )
    
    for par in b_defs[ "beacon_info" ]:
        service_info[ par ] = b_defs[ "beacon_info" ][ par ]
        
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ config[ "info_db" ] ]
    mongo_coll = mongo_db[ 'dbstats' ]
    
    stats = mongo_coll.find_one( { }, sort=[( '_id', -1 )] )

    mongo_client.close( )   

    """podmd
    The counts for the collections (`variants`, `biosamples` etc.) of the
    different datasets are retrieved from the daily updated 
    `progenetix.dbstats` collection.

    For the non-parametrized call of the application, just the basic
    information including variant counts is returned.

    end_podmd"""

    ds_with_counts = [ ]
    for dataset in b_defs[ "beacon_info" ][ "datasets" ]:
        if dataset["id"] in config[ "dataset_ids" ]:
            dataset[ "callCount" ] = stats[ dataset["id"]+"__variants" ][ "count" ]
            dataset[ "variantCount" ] = stats[ dataset["id"]+"__variants" ][ "distincts_count_digest" ]
            dataset[ "sampleCount" ] = stats[ dataset["id"]+"__biosamples" ][ "count" ]
            ds_with_counts.append(dataset)
        
    service_info[ "datasets" ] = ds_with_counts

    print(json.dumps(service_info, indent=4, sort_keys=True, default=str))
  
    return(  )


################################################################################

def create_dataset_response(**kwargs):


	return( kwargs[ "query_results" ] )

################################################################################

def create_beacon_response(**kwargs):

    with open( path.join(path.abspath(kwargs["dir_path"]), "..", "config", "beacon_info.yaml") ) as bc:
        b_defs = yaml.load( bc , Loader=yaml.FullLoader)

    b_response = {}
    
        

    return(  )


################################################################################


