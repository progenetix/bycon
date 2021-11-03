#!/usr/local/bin/python3

import cgi, cgitb, sys
from os import path, environ, pardir

from pymongo import MongoClient
from bson.objectid import ObjectId


# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

################################################################################
################################################################################
################################################################################

"""
https://progenetix.test/beacon/variants/?filters=NCIT:C7712&output=pgxseg&debug=1
http://progenetix.test/cgi/bycon/beaconServer/variants.py?start=0,120000000&end=123000000,124500000&referenceName=8&variantType=DUP&filters=icdom-81703&debug=1
"""

def main():

    variants()
    
################################################################################

def variants():

    byc = initialize_service()
    run_beacon_init_stack(byc)
    run_variants_beacon(byc)
    export_datatable(byc)
    query_results_save_handovers(byc)
    cgi_print_response( byc, 200 )

################################################################################

def run_variants_beacon(byc):

    for i, r_set in enumerate(byc["service_response"]["response"]["result_sets"]):

        results_count = 0
        ds_id = r_set["id"]

        if len(byc["queries"].keys()) > 0:
            execute_bycon_queries( ds_id, byc )
            check_alternative_variant_deliveries(ds_id, byc)
            beacon_res = retrieve_variants(ds_id, byc)
            r_set.update({ "results_handovers": dataset_response_add_handovers(ds_id, byc) })

            for c, c_d in byc["config"]["beacon_counts"].items():
                if c_d["h->o_key"] in byc["dataset_results"][ds_id]:
                    r_c = byc["dataset_results"][ds_id][ c_d["h->o_key"] ]["target_count"]
                    r_set["info"]["counts"].update({ c: r_c })

            if isinstance(beacon_res, list):
                results_count = len( beacon_res )

        else:
            beacon_res, results_count = process_empty_request(ds_id, "variants", byc)
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

def retrieve_variants(ds_id, byc):

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    v_coll = mongo_client[ ds_id ][ "variants" ]

    ds_results = byc["dataset_results"][ds_id]

    if not byc["method"] in byc["this_config"]["all_variants_methods"]:

        if "variants.digest" in ds_results:
            beacon_res = []
            for d in ds_results["variants.digest"]["target_values"]:
                d_vs = v_coll.find({"digest": d })

                v = {
                    "variant_internal_id": d,
                    "variant_type": d_vs[0].get("variant_type", "SNV"),
                    "position":{
                        "assembly_id": "GRCh38",
                        "refseq_id": "chr"+d_vs[0]["reference_name"],
                        "start": [ int(d_vs[0]["start"]) ]
                    },
                    "case_level_data": []
                }

                if "end" in d_vs[0]:
                    v["position"].update({ "end": [ int(d_vs[0]["end"]) ] })

                for v_t in ["variant_type", "reference_bases", "alternate_bases"]:
                    if v_t in d_vs[0]:
                        v.update({ v_t: d_vs[0][v_t] })

                for d_v in d_vs:
                    v["case_level_data"].append(
                        {   
                            "id": d_v["id"],
                            "biosample_id": d_v["biosample_id"],
                            "analysis_id": d_v["callset_id"]
                        }
                    )

                beacon_res.append(v)

            return beacon_res

    return False

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
