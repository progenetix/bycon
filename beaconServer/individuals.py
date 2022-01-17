#!/usr/local/bin/python3

from os import path, pardir
import sys

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd
* <https://progenetix.org/cgi/bycon/services/individuals.py?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.org/beacon/individuals?datasetIds=progenetix&filters=cellosaurus:CVCL_0030>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    individuals()
    
################################################################################

def individuals():

    initialize_service(byc)
    run_beacon_init_stack(byc)

    return_filtering_terms_response(byc)

    run_result_sets_beacon(byc)
    export_datatable(byc)
    check_alternative_variant_deliveries(byc)
    query_results_save_handovers(byc)

    # Phenopackets
    # TODO: very hacky, for testing so far ...

    # if "requestedSchemas" in byc["query_meta"]:

    #     if re.match(r".*?Phenopacket.*?", byc["query_meta"]["requestedSchemas"][0]["schema"]):
            
    #         for i, r_set in enumerate(byc["service_response"]["response"]["result_sets"]):
    #             ds_id = r_set["id"]
    #             ds_results = byc["dataset_results"][ds_id]
    #             results = ds_results_phenopack_individuals(ds_id, ds_results)
    #             byc["service_response"]["response"]["result_sets"][i].update( {"results": results } )
                
    #         byc["service_response"]["meta"].update({ "returned_schemas": byc["query_meta"]["requestedSchemas"][0]["schema"] })
    #         byc["service_response"]["meta"]["received_request_summary"].update({ "requested_schemas": byc["query_meta"]["requestedSchemas"][0]["schema"] })

    check_switch_to_count_response(byc)
    check_switch_to_boolean_response(byc)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
