#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path as path
from os import environ
import sys, os, datetime, logging, argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

# log_file = path.join( path.abspath( dir_path ), '..', "data", "out", "logs", "python_log.txt" )

# logging.basicConfig(
#     filename=log_file,
#     level=logging.INFO) # INFO ERROR

"""podmd

##### Examples

* standard test deletion CNV query
  - <https://bycon.progenetix.org?datasetIds=arraymap&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&startMin=18000000&startMax=21975097&endMin=21967753&endMax=26000000&filters=icdom-94403>
  - <https://bycon.progenetix.org/datasetIds=arraymap,progenetix/assemblyId=GRCh38/includeDatasetResponses=ALL/referenceName=9/variantType=DEL/startMin=18000000/startMax=21975097/endMin=21967753/endMax=26000000/filters=icdom-94403>
* retrieving biosamples w/ a given filter code
  - <https://bycon.progenetix.org?assemblyId=GRCh38/datasetIds=arraymap,progenetix/filters=NCIT:C3326>
* beacon info (i.e. missing parameters return the info)
  - <https://bycon.progenetix.org>
* beacon info (i.e. specific request)
  - <https://bycon.progenetix.org/service-info/>
* precise variant query together with filter
  - <https://bycon.progenetix.org?datasetIds=dipg/assemblyId=GRCh38/includeDatasetResponses=ALL/referenceName=17/start=7577120/referenceBases=G/alternateBases=A/filters=icdot-C71.7>
* retrieving filters
  - <https://bycon.progenetix.org/filtering_terms/>
  - <https://bycon.progenetix.org/filtering_terms/prefixes=PMID/>
  - <https://bycon.progenetix.org/filtering_terms/prefixes=NCIT,icdom/>
  - <https://bycon.progenetix.org/filtering_terms/prefixes=NCIT,icdom,icdot/datasetId=dipg/>

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-t", "--test", action='store_true', help="test from command line with default parameters")
    parser.add_argument("-i", "--info", action='store_true', help="test from command line for info")
    parser.add_argument("-n", "--filtering_terms", action='store_true', help="test filtering term response")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    byconplus()
    
################################################################################

def byconplus():

    # last_time = datetime.datetime.now()
    # logging.info("Start: {}".format(last_time))
    
    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( *config[ "paths" ][ "web_temp_dir_abs" ] )

    # input / definitions
    form_data = cgi_parse_query()
    args = _get_args()
    rest_pars = cgi_parse_path_params( "byconplus" )

    # logging.info("Init steps: {}".format(datetime.datetime.now()-last_time))
    # last_time = datetime.datetime.now()

    # TODO: "byc" becoming a proper object?!
    byc = {
        "config": config,
        "args": args,
        "form_data": form_data,
        "rest_pars": rest_pars,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "datasets_info": read_datasets_info( **config[ "paths" ] ),
        "service_info": read_service_info( **config[ "paths" ] ),
        "beacon_info": read_beacon_info( **config[ "paths" ] ),
        "beacon_paths": read_beacon_api_paths( **config[ "paths" ] ),
        "get_filters": False
    }

    byc.update( { "dbstats": dbstats_return_latest( **byc ) } )
    byc["beacon_info"].update( { "datasets": update_datasets_from_dbstats(**byc) } )
    byc.update( { "endpoint": beacon_get_endpoint(**byc) } )

    for par in byc[ "beacon_info" ]:
        byc[ "service_info" ][ par ] = byc[ "beacon_info" ][ par ]

    respond_empty_request(**byc)
    respond_get_datasetids_request(**byc)
    respond_filtering_terms_request(**byc)
    respond_service_info_request(**byc)

    # adding arguments for querying / processing data
    byc.update( { "h->o": read_handover_info( **config[ "paths" ] ) } )
    byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
    byc.update( { "filters":  parse_filters( **byc ) } )
    byc[ "variant_defs" ], byc[ "variant_request_types" ] = read_variant_definitions( **byc )
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } ) 
    byc.update( { "queries": create_queries_from_filters( **byc ) } )

    if byc["variant_request_type"] in byc["variant_request_types"].keys():
        variant_query_generator = "create_"+byc["variant_request_type"]+"_query"
        byc["queries"].update( { "variants": getattr(cgi_parse_variant_requests, variant_query_generator)( byc["variant_request_type"], byc["variant_pars"] ) } )

    # fallback - but maybe shouldbe an error response?
    if not byc[ "queries" ]:
        cgi_print_json_response(byc["service_info"])
            
    # logging.info("Parsing steps: {}".format(datetime.datetime.now()-last_time))

    dataset_responses = [ ]

    for ds_id in byc[ "dataset_ids" ]:
        byc.update( { "ds_id": ds_id, "last_time": datetime.datetime.now() } )
        byc.update( { "query_results": execute_bycon_queries( **byc ) } )
        dataset_responses.append( create_dataset_response( **byc ) )   

        # logging.info("Query: {}: {}".format(byc['queries'], datetime.datetime.now()-last_time))
        # last_time = datetime.datetime.now()

    byc.update( { "dataset_responses": dataset_responses } )
    beacon_response = create_beacon_response(**byc)
    
    cgi_print_json_response(beacon_response)

    # logging.info("Query steps: {}".format(datetime.datetime.now()-last_time))
    # last_time = datetime.datetime.now()
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
