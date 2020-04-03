#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path as path
import sys

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py?assemblyId=GRCh38&datasetIds=progenetix&filters=icdom-85,icdot-C54&referenceName=9&startMin=18000000&startMax=24000000&endMin=22000000&endMax=2600000&variantType=DEL
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py?filters=NCIT:C3326&referenceName=9&startMin=18000000&startMax=24000000&endMin=22000000&endMax=2600000&variantType=DEL
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py?datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&startMin=17999999&startMax=21975097&endMin=21967753&endMax=26000000&referenceBases=N&filters=icdom-94403&filters=geolat%3A49%2Cgeolong%3A8.69%2Cgeodist%3A2000000&
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py/service-info/
"""

################################################################################
################################################################################
################################################################################

# cgitb.enable()  # for debugging

################################################################################

def main():

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
    service_info = return_beacon_info( **{ "config": config } )

    kwargs = { "config": config, "opts": opts, "form_data": form_data, "service_info": service_info }

    dataset_ids = get_dataset_ids( **kwargs )

    kwargs["filter_defs"] = read_filter_definitions( **kwargs )
    kwargs["filters"] = parse_filters( **kwargs )    
    kwargs["variant_defs"], kwargs["variant_request_types"] = read_variant_definitions( **kwargs )
    kwargs["variant_pars"] = parse_variants( **kwargs )
    
    variant_request_type = get_variant_request_type( **kwargs )       
    queries = create_queries_from_filters( **kwargs )

    if variant_request_type in kwargs["variant_request_types"]:
        variant_query_generator = "create_"+variant_request_type+"_query"
        queries["variants"] = getattr(cgi_parse_variant_requests, variant_query_generator)(variant_request_type, kwargs["variant_pars"])

    # TODO: earlier catch for empty call => info
    if not queries:
        print(json.dumps(service_info, indent=4, sort_keys=True, default=str))
        exit()
    
    dataset_responses = [ ]

    for ds in dataset_ids:
        kwargs = { "config": config, "queries": queries, "dataset_id": ds }
        kwargs[ "query_results" ] = execute_bycon_queries(**kwargs)
        dataset_responses.append( create_dataset_response(**kwargs) )   
    
    kwargs = { "config": config, "service_info": service_info, "dataset_responses": dataset_responses }
    beacon_response = create_beacon_response(**kwargs)
    
    print(json.dumps(beacon_response, indent=4, sort_keys=True, default=str))
#     print(json.dumps(queries))
    
    # for res_key in dataset_responses[0]:
    #     print(res_key+": "+str(len(dataset_responses[0][ res_key ])))
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
