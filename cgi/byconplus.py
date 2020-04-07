#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path as path
import sys
import datetime
import logging

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

log_file = path.join( path.abspath( dir_path ), '..', "data", "out", "logs", "python_log.txt" )

logging.basicConfig(
    filename=log_file,
    level=logging.ERROR) # INFO ERROR

"""
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py?datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&startMin=17999999&startMax=21975097&endMin=21967753&endMax=26000000&referenceBases=N&filters=icdom-94403
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py?assemblyId=GRCh38&datasetIds=arraymap,progenetix&filters=NCIT:C3326
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py?assemblyId=GRCh38&datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&startMin=17999999&startMax=21975097&endMin=21967753&endMax=26000000&referenceBases=N&filters=icdom-94403&filters=geolat%3A49%2Cgeolong%3A8.69%2Cgeodist%3A2000000&
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py/service-info/
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py?datasetIds=dipg&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&start=7577120&referenceBases=G&alternateBases=A&filters=icdot-C71.7&
"""

################################################################################
################################################################################
################################################################################

# cgitb.enable()  # for debugging

################################################################################

def main():

    last_time = datetime.datetime.now()
    logging.info("Start: {}".format(last_time))

    print('Content-Type: application/json')
    # print('Content-Type: text')
    print()
#     read_beacon_v2_spec(dir_path)
    
    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.abspath( config[ "paths" ][ "web_temp_dir_abs" ] )

    # input & definitions
    form_data = cgi_parse_query()
    opts, args = get_cmd_args()

    logging.info("Init steps: {}".format(datetime.datetime.now()-last_time))
    last_time = datetime.datetime.now()

    # TODO: "byc" becoming a proper object?!
    byc = {
        "config": config,
        "opts": opts,
        "form_data": form_data
    }
    byc.update( { "service_info": return_beacon_info( **byc ) } )    
    byc.update( { "dataset_ids": get_dataset_ids( **byc ) } )
    byc.update( { "filter_defs": read_filter_definitions( **byc ) } )
    byc.update( { "filters":  parse_filters( **byc ) } )
    byc[ "variant_defs" ], byc[ "variant_request_types" ] = read_variant_definitions( **byc )
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } ) 
    byc.update( { "queries": create_queries_from_filters( **byc ) } )

    if byc["variant_request_type"] in byc["variant_request_types"]:
        variant_query_generator = "create_"+byc["variant_request_type"]+"_query"
        byc["queries"].update( { "variants": getattr(cgi_parse_variant_requests, variant_query_generator)( byc["variant_request_type"], byc["variant_pars"] ) } )

    # TODO: earlier catch for empty call => info
    if not byc[ "queries" ]:
        print(json.dumps(service_info, indent=4, sort_keys=True, default=str))
        exit()
    
    logging.info("Parsing steps: {}".format(datetime.datetime.now()-last_time))

    dataset_responses = [ ]

    for ds in byc[ "dataset_ids" ]:
        byc.update( { "dataset_id": ds, "last_time": datetime.datetime.now() } )
        byc.update( { "query_results": execute_bycon_queries( **byc ) } )
        dataset_responses.append( create_dataset_response( **byc ) )   

        logging.info("Query: {}: {}".format(byc['queries'], datetime.datetime.now()-last_time))
        last_time = datetime.datetime.now()
    
    byc.update( { "dataset_responses": dataset_responses } )
    beacon_response = create_beacon_response(**byc)
    
    print(json.dumps(beacon_response, indent=4, sort_keys=True, default=str))

    logging.info("Query steps: {}".format(datetime.datetime.now()-last_time))
    last_time = datetime.datetime.now()
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
