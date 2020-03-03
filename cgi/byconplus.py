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
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py?filters=icdom-85,icdot-C54&referenceName=9&startMin=18000000&startMax=24000000&endMin=22000000&endMax=2600000&variantType=DEL
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py
https://progenetix.test/cgi-bin/bycon/cgi/byconplus.py/service-info/
"""

################################################################################
################################################################################
################################################################################

cgitb.enable()  # for debugging

################################################################################

def main():

    print('Content-Type: text')
    print()
    
#     read_beacon_v2_spec(dir_path)
    
    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "mod_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.abspath( config[ "paths" ][ "web_temp_dir_abs" ] )

    form_data = cgi_parse_query()
    
    dataset_ids = get_dataset_ids(form_data)
    # TODO: proper dataset_ids parsing & processing
    dataset_ids = [ "arraymap" ]

    filter_defs = read_filter_definitions( **{ "config": config } )
    filters = parse_filters(form_data)
    
    variant_defs, variant_request_types = read_variant_definitions( **{ "config": config } )
    variant_pars = parse_variants(form_data, variant_defs)
    variant_request_type = get_variant_request_type(variant_defs, variant_pars, variant_request_types)
        
    kwargs = { "config": config, "filter_defs": filter_defs, "filters": filters }
    queries = create_queries_from_filters(**kwargs)
    
    if variant_request_type in variant_request_types:
        variant_query_generator = "create_"+variant_request_type+"_query"
        queries["variants"] = getattr(cgi_parse_variant_requests, variant_query_generator)(variant_request_type, variant_pars)
    
    # TODO: earlier catch for empty call => info
    if not queries:
        return_beacon_info( **{ "config": config } )
        exit()
    
    dataset_responses = [ ]

    for ds in dataset_ids:
        kwargs = { "config": config, "queries": queries, "dataset": ds }
        kwargs[ "query_results" ] = execute_bycon_queries(**kwargs)
        dataset_responses.append( create_dataset_response(**kwargs) )   
    
    kwargs = { "config": config, "dataset_responses": dataset_responses }
    create_beacon_response(**kwargs)
    
#     print(json.dumps(dataset_responses, indent=4, sort_keys=True, default=str))
#     print(json.dumps(queries))
    
    for res_key in dataset_responses[0]:
        print(res_key+": "+str(len(dataset_responses[0][ res_key ])))
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
