#!/usr/local/bin/python3

import cgi, cgitb
import re, json
from os import path, pardir
import sys
from pymongo import MongoClient

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd
* <https://progenetix.org/services/geolocations?city=zurich>
* <https://progenetix.org/services/geolocations?geoLongitude=8.55&geoLatitude=47.37&geoDistance=100000>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    geolocations()
    
################################################################################

def geolocations():

    initialize_service(byc)

    # for the geolocs database, not the provenance object
    byc["geoloc_definitions"]["geo_root"] = "geo_location"
    
    create_empty_service_response(byc)

    query, geo_pars = geo_query( byc )
    for g_k, g_v in geo_pars.items():
        response_add_received_request_summary_parameter(byc, g_k, g_v)

    if len(query.keys()) < 1:
        response_add_error(byc, 422, "No query generated - missing or malformed parameters" )
    
    cgi_break_on_errors(byc)

    results, e = mongo_result_list( byc["dataset_ids"][0], byc["geo_coll"], query, { '_id': False } )
    if e:
        response_add_error(byc, 422, e)
    
    cgi_break_on_errors(byc)

    if "text" in byc["output"]:
        open_text_streaming(byc["env"])
        for g in results:
            s_comps = []
            for k in ["city", "country", "continent"]:
                s_comps.append(str(g["geo_location"]["properties"].get(k, "")))
            s_comps.append(str(g.get("id", "")))
            for l in g["geo_location"]["geometry"].get("coordinates", [0,0]):
                s_comps.append(str(l))
            print("\t".join(s_comps))
        exit()

    populate_service_response( byc, results)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
