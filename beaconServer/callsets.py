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

    byc = initialize_service()
    run_beacon_init_stack(byc)
    run_result_sets_beacon("callsets", byc)
    export_datatable(byc)

    ############################################################################
    # TODO: Fix for multiple datasets
    check_alternative_callset_deliveries(byc)
    ############################################################################

    query_results_save_handovers(byc)
    cgi_print_response( byc, 200 )
    cgi_break_on_errors(byc)

    return byc

################################################################################

def retrieve_analyses(ds_id, byc):

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    bs_coll = mongo_client[ ds_id ][ "callsets" ]

    ds_results = byc["dataset_results"][ds_id]
    r_key = "callsets._id"

    if r_key in ds_results:
        beacon_res = []
        for b in bs_coll.find({"_id":{"$in": ds_results[ r_key ]["target_values"] }}):
            beacon_res.append(b)

        return beacon_res

    return False

################################################################################
################################################################################
############################################################################

if __name__ == '__main__':
    main()
