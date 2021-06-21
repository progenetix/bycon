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

    byc = initialize_service()
    run_beacon_init_stack(byc)
    run_beacon(byc)
    export_datatable(byc)

    # Phenopackets

    query_results_save_handovers(byc)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
