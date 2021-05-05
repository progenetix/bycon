#!/usr/local/bin/python3

from os import path, pardir
import sys

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd
* <https://progenetix.org/cgi/bycon/services/biosamples.py?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.org/beacon/biosamples?datasetIds=progenetix&filters=cellosaurus:CVCL_0030>
* <https://progenetix.org/beacon/biosamples/pgxbs-kftva5c8/variants/>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    biosamples()
    
################################################################################

def biosamples():

    byc = initialize_service()
    run_beacon_init_stack(byc)
    run_beacon_one_dataset(byc)

    query_results_save_handovers(byc)

    # TODO: This is a stop-gap for Progenetix, adding the original structure
    # for parsing by the front-end, for now

    if "includeDatasetResponses" in byc["form_data"]:
    	byc["service_response"]["response"].update({
    		"datasetAlleleResponses": [ { "datasetId": byc[ "dataset_ids" ][0], "datasetHandover": byc["service_response"]["response"]["results_handover"] }]})
    	for c_k, c_v in byc["service_response"]["response"]["info"]["counts"].items():
    		byc["service_response"]["response"]["datasetAlleleResponses"][0].update({ c_k: c_v })
    	for k in ["exists", "results"]:
    		byc["service_response"]["response"]["datasetAlleleResponses"][0].update({ k: byc["service_response"]["response"][k] })
    	for d in ["results", "results_handover"]:
    		del(byc["service_response"]["response"][d])

 
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
