#!/usr/local/bin/python3

from os import path, pardir
import sys

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd

* <https://progenetix.org/cgi/bycon/beaconServer/biosamples.py?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.org/beacon/biosamples?datasetIds=progenetix&filters=cellosaurus:CVCL_0030>
* https://progenetix.org/cgi/bycon/beaconServer/biosamples.py?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.org/cgi/bycon/beaconServer/biosamples.py?datasetIds=progenetix&filters=cellosaurus:CVCL_0030
* <https://progenetix.org/beacon/biosamples/pgxbs-kftva5c8/variants/>
* <http://progenetix.test/beacon/biosamples/?filters=icdom-85002&output=table&debug=1>
* <http://progenetix.test/beacon/biosamples/?datasetIds=progenetix&assemblyId=GRCh38&referenceName=9&variantType=DEL&filterLogic=AND&start=21500000&start=21975098&end=21967753&end=22500000&filters=NCIT%3AC3058>

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
    return_filtering_terms_response(byc)
    run_result_sets_beacon(byc)
    export_datatable(byc)
    check_alternative_variant_deliveries(byc)
    query_results_save_handovers(byc)
    check_switch_to_count_response(byc)
    check_switch_to_boolean_response(byc)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
