#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path, environ, pardir
import sys, datetime, argparse
from bson.objectid import ObjectId

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )
sys.path.append( pkg_path )
from bycon.lib import *
from service_utils import *

################################################################################
################################################################################
################################################################################

"""
https://progenetix.test/services/variants/?datasetIds=progenetix&filters=NCIT:C7712&method=pgxseg&debug=1
"""

def main():

    variants()
    
################################################################################

def variants():

    byc = initialize_service()

    parse_beacon_schema(byc)

    initialize_beacon_queries(byc)

    r = create_empty_service_response(byc)
    response_collect_errors(r, byc)
    cgi_break_on_errors(r, byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(r, "dataset", ds_id )
    execute_bycon_queries( ds_id, byc )

    ############################################################################

    mongo_client = MongoClient()
    v_coll = mongo_client[ ds_id ][ "variants" ]
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]
    response = [ ]

    ############################################################################

    if byc["method"] in byc["these_prefs"]["all_variants_methods"]:

        vs = [ ]
        for bs_id in byc["query_results"]["bs.id"][ "target_values" ]:
            for v in v_coll.find(
                    {"biosample_id": bs_id },
                    { "_id": 0, "assembly_id": 0, "digest": 0, "callset_id": 0 }
            ):
                val = ""
                if "info" in v:
                    if "cnv_value" in v["info"]:
                        if isinstance(v["info"]["cnv_value"],float):
                            val = '{:.3f}'.format(v["info"]["cnv_value"])
                v["start"] = int(v["start"])
                v["end"] = int(v["end"])
                vs.append(v)

        r["response"]["info"].update({
            "variant_count": len(vs),
            "biosample_count": byc["query_results"]["bs.id"][ "target_count" ]
        })

        if "callsetsvariants" in byc["method"]:
            open_json_streaming(r, "variants.json")
        elif "pgxseg" in byc["method"]:
            open_text_streaming()
            for d in ["id", "assemblyId"]:
                print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
            for m in ["variant_count", "biosample_count"]:
                print("#meta=>{}={}".format(m, r["response"]["info"][m]))
            print("#meta=>filters="+','.join(r["meta"]["received_request"]["filters"]))
            for bs_id in byc["query_results"]["bs.id"][ "target_values" ]:
                bs = bs_coll.find_one( { "id": bs_id } )
                h_line = "#sample_id={}".format(bs_id)
                for b_c in bs[ "biocharacteristics" ]:
                    if "NCIT:C" in b_c["id"]:
                        h_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(h_line, b_c["id"], b_c["label"], b_c["id"], b_c["label"])
                print(h_line)
            print("{}\t{}\t{}\t{}\t{}\t{}".format("biosample_id", "reference_name", "start", "end", "variant_type", "log2" ) )

        # faster to loop over the biosamples again instead of over each variant
        # TODO: get rid of the original vs._id generation in query_execution
        # ... which here basically only would be needed for the variant count
        for v in vs:
            if "callsetsvariants" in byc["method"]:
                print(json.dumps(v, indent=None, sort_keys=False, default=str, separators=(',', ':'))+",")
            elif "pgxseg" in byc["method"]:
                print("{}\t{}\t{}\t{}\t{}\t{}".format(bs_id, v["reference_name"], v["start"], v["end"], v["variant_type"], val) )

        if "callsetsvariants" in byc["method"]:
            close_json_streaming()
        elif "pgxseg" in byc["method"]:
            close_text_streaming()

    ############################################################################

    query_results_save_handovers(byc)

    access_id = byc["query_results"]["vs._id"][ "id" ]

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        response_add_error(r, 422, e )

    populate_service_response(r, response_map_results(h_o_d, byc))
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

def open_json_streaming(response, filename="data.json"):

    print('Content-Type: application/json')
    print('Content-Disposition: attachment; filename="{}"'.format(filename))
    print('status: 200')
    print()
    print("{")
    print('"meta":')

    print(json.dumps(response["meta"], indent=None, sort_keys=True, default=str)+",")
    print('"response": {')
    print('"results": [')

################################################################################

def close_json_streaming():
    print("],")
    print("}")
    print("}")
    exit()

################################################################################

def open_text_streaming(filename="data.pgxseg"):

    print('Content-Type: text/pgxseg')
    print('Content-Disposition: attachment; filename="{}"'.format(filename))
    print('status: 200')
    print()

################################################################################

def close_text_streaming():

    print()
    exit()

################################################################################
################################################################################



if __name__ == '__main__':
    main()
