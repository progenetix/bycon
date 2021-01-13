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
from bycon.lib.cgi_utils import cgi_parse_query,cgi_print_json_response
from bycon.lib.read_specs import read_local_prefs,read_bycon_configs_by_name
from bycon.lib.query_generation import geo_query
from bycon.lib.query_execution import mongo_result_list
from lib.service_utils import *

"""podmd
* <https://progenetix.org/services/geolocations?city=zurich>
* <https://progenetix.org/services/geolocations?geolongitude=8.55&geolatitude=47.37&geodistance=100000>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    geolocations("geolocations")
    
################################################################################

def geolocations(service):

    byc = {
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        "geoloc_definitions": read_bycon_configs_by_name( "geoloc_definitions" ),
        "form_data": cgi_parse_query(),
        "errors": [ ],
        "warnings": [ ]
    }

    byc["geoloc_definitions"]["geo_root"] = ""

    these_prefs = read_local_prefs( service, dir_path )
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )
    
    # response prototype
    r = create_empty_service_response(**these_prefs)

    query, geo_pars = geo_query( **byc )
    for g_k, g_v in geo_pars.items():
        r["meta"]["parameters"].append( { g_k: g_v } )

    if len(query.keys()) < 1:
        r["meta"]["errors"].append( "No query generated - missing or malformed parameters" )
        cgi_print_json_response( byc[ "form_data" ], r, 422 )

    results, error = mongo_result_list( byc["geo_db"], byc["geo_coll"], query, { '_id': False } )
    if error:
        r["meta"]["errors"].append( error )
        cgi_print_json_response( byc[ "form_data" ], r, 422 )

    populate_service_response(r, results)
    cgi_print_json_response( byc[ "form_data" ], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
