#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path, environ, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib import *
from lib.service_utils import *

################################################################################
################################################################################
################################################################################

def main():

    variants("variants")
    
################################################################################

def variants(service):

    byc = initialize_service(service)

    r = create_empty_service_response(byc)

    if "do" in byc["form_data"]:
        do = byc["form_data"].getvalue("do")
        access_id = byc["form_data"].getvalue("accessid")

        response_add_parameter(r, "accessid", access_id)

        if do == "callsetsvariants":

            open_json_streaming(r, "variants.json")

            results = [ ]

            count = 0;
            biosamples = { }

            h_o, e = retrieve_handover( access_id, **byc )
            mongo_client = MongoClient()
            ds_id = h_o["source_db"]
            cs_coll = mongo_client[ ds_id ][ "callsets" ]
            v_coll = mongo_client[ ds_id ][ "variants" ]
            for cs_id in h_o["target_values"]:
                cs = cs_coll.find_one( { "_id": cs_id } )
                v_q = { "callset_id": cs["id"] }
                for v in v_coll.find( v_q, { '_id': False, 'digest': False, 'updated': False, 'assembly_id': False, 'callset_id': False, 'info': False  } ):
                    v["start"] = int(v["start"])
                    v["end"] = int(v["end"])
                    if "biosample_id" in v:
                        biosamples.update({ v["biosample_id"] : 1 } )
                    count = count + 1
                    print(json.dumps(v, indent=None, sort_keys=False, default=str)+",")

            info = { "variant_count": count, "biosample_count": len(biosamples.keys()) }

            close_json_streaming(info)

    select_dataset_ids(byc)
    beacon_check_dataset_ids(byc)
    get_filter_flags(byc)
    parse_filters(byc)

    parse_variants(byc)
    get_variant_request_type(byc)
    generate_queries(byc)

    response_collect_errors(r, byc)
    cgi_break_on_errors(r, byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(r, "dataset", ds_id )

    execute_bycon_queries( ds_id, byc )
    query_results_save_handovers(byc)

    access_id = byc["query_results"]["vs._id"][ "id" ]

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        response_add_error(r, e)

    cgi_break_on_errors(r, byc)

    populate_service_response(r, response_map_results(h_o_d, byc))
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

def open_json_streaming(response, filename):

    if not filename:
        filename = "data.json"

    print('Content-Type: application/json')
    print('Content-Disposition: attachment; filename="{}"'.format(filename))
    print('status: 200')
    print()
    print("{")
    print('"meta":')

    print(json.dumps(response["meta"], indent=None, sort_keys=True, default=str)+",")
    print('"response": {')
    print('"results": [')

def close_json_streaming(info):
    print("],")
    print('"info":')
    print(json.dumps(info, indent=None, sort_keys=True, default=str))
    print("}")
    print("}")
    exit()

################################################################################
################################################################################



if __name__ == '__main__':
    main()
