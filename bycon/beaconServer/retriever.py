#!/usr/bin/env python3

import sys
from os import path, environ, pardir
from copy import deepcopy
from liftover import get_lifter

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""podmd

#### Tests

* http://progenetix.org/cgi/bycon/beaconServer/retriever.py?debug=&selectedBeacons=progenetixTest&url=http%3A//progenetix.test/beacon/g_variants/%3FdatasetIds%3Dprogenetix%26assemblyId%3DGRCh38%26referenceName%3D17%26variantType%3DDEL%26start%3D7500000%252C7676592%26end%3D7669607%252C7800000
"""

################################################################################
################################################################################
################################################################################

def main():

    retriever()
   
################################################################################

def retriever():

    initialize_bycon_service(byc, "aggregator")
    parse_filters(byc)
    parse_variant_parameters(byc)
    generate_genomic_intervals(byc)
    create_empty_service_response(byc)    

    cgi_break_on_errors(byc)

    b = byc["form_data"].get("selected_beacons", [])
    url = byc["form_data"].get("url", "")
    # print(url)
    if len(b) != 1:
        print_text_response('not a single "selectedBeacons" value')
    byc["service_config"].update({"selected_beacons": b})
    b = b[0]
    if not "http" in url:
        print_text_response('url seems missing / incomplete')    
    b_p = byc["service_config"]["beacon_params"]["instances"]
    if not b in b_p.keys():
        print_text_response(f'"{b}"is not in available beacon definitions')

    byc["service_response"]["meta"]["received_request_summary"]["requested_granularity"] ="boolean"
    check_switch_to_boolean_response(byc)
    byc["service_response"].update({"response": { "response_sets": [] }})

    ext_defs = b_p[b]

    # TODO: extract dataset id from URL using the ext_defs parameter mapping
    ds_id = byc["form_data"].get("dataset_ids", [])
    if len(ds_id) != 1:
        ds_id = ext_defs["dataset_ids"]
    ds_id = ds_id[0]

    resp_start = time.time()
    # print_text_response(url)
    r = retrieve_beacon_response(url, byc)
    resp_end = time.time()
    # prjsoncam(r)
    # print(url)
    r_f = format_response(r, url, ext_defs, ds_id, byc)
    r_f["info"].update({"response_time": "{}ms".format(round((resp_end - resp_start) * 1000, 0)) })
    byc["service_response"]["response"]["response_sets"].append(r_f)

    for r in byc["service_response"]["response"]["response_sets"]:
        if r["exists"] is True:
            byc["service_response"]["response_summary"].update({"exists": True})
            continue

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
