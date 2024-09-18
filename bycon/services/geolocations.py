#!/usr/bin/env python3
import re, json, sys
from os import path, environ
from pymongo import MongoClient

from bycon import *

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from geomap_utils import *
from service_helpers import *
from service_response_generation import *

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
    try:
        geolocations()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def geolocations():
    initialize_bycon_service()

    BYC["geoloc_definitions"].update({"geo_root": "geo_location"})
    BYC_PARS.update({"plot_type": "geomapplot"})

    r = ByconautServiceResponse()
    # TODO: make the input parsing a class
    if "inputfile" in BYC_PARS:
        results = read_geomarker_table_web()
    else:
        query, geo_pars = geo_query()
        if not query:
            BYC["ERRORS"].append("No query generated - missing or malformed parameters")
        else:
            results = mongo_result_list(SERVICES_DB, GEOLOCS_COLL, query, { '_id': False } )
    if len(BYC["ERRORS"]) > 0:
        BeaconErrorResponse().response(422)

    if "map" in BYC_PARS.get("plot_type", "___none___"):
        ByconMap(results).printMapHTML()

    if len(results) == 1:
        if "geo_distance" in BYC_PARS:
            l_l = results[0]["geo_location"]["geometry"]["coordinates"]
            geo_pars = {
                "geo_longitude": l_l[0],
                "geo_latitude": l_l[1],
                "geo_distance": int(BYC_PARS["geo_distance"])
            }
            query = return_geo_longlat_query(geo_root, geo_pars)
            results = mongo_result_list(SERVICES_DB, GEOLOCS_COLL, query, { '_id': False } )
    if len(BYC["ERRORS"]) > 0:
        e_r = BeaconErrorResponse().error(422)
        print_json_response(e_r)

    if "text" in BYC_PARS.get("output", "___none___"):
        open_text_streaming()
        for g in results:
            s_comps = []
            for k in ["city", "country", "continent"]:
                s_comps.append(str(g["geo_location"]["properties"].get(k, "")))
            s_comps.append(str(g.get("id", "")))
            for l in g["geo_location"]["geometry"].get("coordinates", [0,0]):
                s_comps.append(str(l))
            print("\t".join(s_comps))
        exit()

    print_json_response(r.populatedResponse(results))


################################################################################
################################################################################

if __name__ == '__main__':
    main()
