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
    run_biosamples_beacon(byc)
    export_datatable(byc)
    query_results_save_handovers(byc)
    cgi_print_response( byc, 200 )

################################################################################

def run_biosamples_beacon(byc):

    for i, r_set in enumerate(byc["service_response"]["response"]["result_sets"]):

        results_count = 0
        ds_id = r_set["id"]
        
        if len(byc["queries"].keys()) > 0:
            execute_bycon_queries( ds_id, byc )
            beacon_res = retrieve_biosamples(ds_id, byc)
            r_set.update({ "results_handovers": dataset_response_add_handovers(ds_id, byc) })
            for c, c_d in byc["config"]["beacon_counts"].items():
                if c_d["h->o_key"] in byc["dataset_results"][ds_id]:
                    r_c = byc["dataset_results"][ds_id][ c_d["h->o_key"] ]["target_count"]
                    r_set["info"]["counts"].update({ c: r_c })
            if isinstance(beacon_res, list):
                results_count = len( beacon_res )
        else:
            beacon_res, results_count = process_empty_request(ds_id, "biosamples", byc)
            byc["service_response"]["meta"]["received_request_summary"].update({"pagination":{"limit": 1, "skip": 0}})

        if isinstance(beacon_res, list):
            r_set.update({"results_count": results_count })
            if results_count > 0:

                byc["service_response"]["response_summary"]["num_total_results"] += results_count
                r_set.update({ "exists": True, "results": beacon_res })

                if byc["pagination"]["limit"] > 0:
                    res_range = _pagination_range(results_count, byc)
                    r_set.update({ "results": beacon_res[res_range[0]:res_range[-1]] })

        byc["service_response"]["response"]["result_sets"][i] = r_set

    if byc["service_response"]["response_summary"]["num_total_results"] > 0:
        byc["service_response"]["response_summary"].update({"exists": True })
        response_add_error(byc, 200)

    cgi_break_on_errors(byc)

    return byc

################################################################################

def retrieve_biosamples(ds_id, byc):

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]

    ds_results = byc["dataset_results"][ds_id]
    r_key = "biosamples._id"

    if r_key in ds_results:
        beacon_res = []
        for b in bs_coll.find({"_id":{"$in": ds_results[ r_key ]["target_values"] }}):
            beacon_res.append(b)

        return beacon_res

    return False

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
