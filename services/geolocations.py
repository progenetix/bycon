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
* <https://progenetix.org/services/geolocations?geoLongitude=8.55&geoLatitude=47.37&geoDistance=100000&output=map>
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

    results = []

    if "file" in byc["form_data"]:
        if "http" in byc["form_data"]["file"]:
            lf = re.split("\n", requests.get(byc["form_data"]["file"]).text)
            lf.pop(0)

            markers = {}
            for line in lf:

                line += "\t\t\t"
                l_l = line.split("\t")
                if len(l_l) < 6:
                    continue
                group_label, group_lat, group_lon, item_size, item_label, item_link, markerType, *_ = l_l[:7]

                if not re.match(r'^\-?\d+?(?:\.\d+?)?$', group_lat):
                    continue
                if not re.match(r'^\-?\d+?(?:\.\d+?)?$', group_lon):
                    continue
                if not re.match(r'^\d+?(?:\.\d+?)?$', item_size):
                    item_size = 1

                m_k = "{}::{}::{}".format(group_label, group_lat, group_lon)
                if markerType not in ["circle", "marker"]:
                    markerType = "circle"

                # TODO: load schema for this
                if not m_k in markers.keys():
                    markers[m_k] = {
                        "geo_location": {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [ float(group_lon), float(group_lat) ]
                            },
                            "properties": {
                                "city": None,
                                "country": None,
                                "label": group_label,
                                "marker_type": markerType,
                                "marker_count": 0,
                                "items": []
                            }
                        }
                    }

                g_l_p = markers[m_k]["geo_location"]["properties"]
                g_l_p["marker_count"] += float(item_size)

                if len(item_label) > 0:
                    if "http" in item_link:
                        item_label = "<a href='{}'>{}</a>".format(item_link, item_label)
                    g_l_p["items"].append(item_label)

            for m_k, m_v in markers.items():
                results.append(m_v)

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
