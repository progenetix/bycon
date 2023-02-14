#!/usr/bin/env python3

import cgi, cgitb
import re, json
from os import path, pardir
import sys
from pymongo import MongoClient

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""podmd
* <https://progenetix.org/services/geolocations?city=zurich>
* <https://progenetix.org/services/geolocations?geoLongitude=8.55&geoLatitude=47.37&geoDistance=100000>
* <https://progenetix.org/services/geolocations?geoLongitude=8.55&geoLatitude=47.37&geoDistance=100000&output=map>
* <http://progenetix.org/services/geolocations?bubble_stroke_weight=0&marker_scale=5&canvas_w_px=1000&file=https://raw.githubusercontent.com/progenetix/pgxMaps/main/rsrc/locationtest.tsv&debug=&output=map&help=true>
* <http://progenetix.org/cgi/bycon/services/geolocations.py?city=New&ISO3166alpha2=UK&output=map&markerType=marker>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    geolocations()
    
################################################################################

def geolocations():

    initialize_bycon_service(byc)

    # for the geolocs database, not the provenance object
    byc["geoloc_definitions"]["geo_root"] = "geo_location"
    
    create_empty_service_response(byc)

    # TODO: move the map table reading to a sane place 
    if "file" in byc["form_data"]:
        results = read_geomarker_table_web(byc)

    else:

        query, geo_pars = geo_query( byc )
        for g_k, g_v in geo_pars.items():
            response_add_received_request_summary_parameter(byc, g_k, g_v)

        if len(query.keys()) < 1:
            response_add_error(byc, 422, "No query generated - missing or malformed parameters" )
        
        cgi_break_on_errors(byc)

        results, e = mongo_result_list( byc["dataset_ids"][0], byc["geo_coll"], query, { '_id': False } )
        response_add_error(byc, 422, e)

    print_map_from_geolocations(byc, results)

    if len(results) == 1:
        if "geo_distance" in byc["form_data"]:
            l_l = results[0]["geo_location"]["geometry"]["coordinates"]
            geo_pars = {
                "geo_longitude": l_l[0],
                "geo_latitude": l_l[1],
                "geo_distance": int(byc["form_data"]["geo_distance"])
            }
            query = return_geo_longlat_query(byc["geoloc_definitions"]["geo_root"], geo_pars)
            results, e = mongo_result_list( byc["dataset_ids"][0], byc["geo_coll"], query, { '_id': False } )
            response_add_error(byc, 422, e)
    
    cgi_break_on_errors(byc)

    if "text" in byc["output"]:
        open_text_streaming(byc["env"], "browser")
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
