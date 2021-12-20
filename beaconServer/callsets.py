#!/usr/local/bin/python3

from os import path, pardir
import sys

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd
* <https://progenetix.org/beacon/callsets/?referenceName=17&variantType=DEL&start=5000000&start=7676592&end=7669607&end=10000000&filters=cellosaurus&output=pgxmatrix>
* <https://progenetix.org/beacon/callsets?datasetIds=progenetix&filters=cellosaurus:CVCL_0030>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    callsets()
    
################################################################################

def callsets():

    initialize_service(byc)
    run_beacon_init_stack(byc)
    return_filtering_terms_response(byc)
    run_result_sets_beacon(byc)
    export_datatable(byc)
    check_alternative_variant_deliveries(byc)

    ############################################################################
    # TODO: Fix for multiple datasets
    check_alternative_callset_deliveries(byc)
    ############################################################################

    query_results_save_handovers(byc)
    check_switch_to_count_response(byc)
    check_switch_to_boolean_response(byc)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################
############################################################################

if __name__ == '__main__':
    main()
