#!/usr/local/bin/python3

import cgi, cgitb
import re, json
import sys, os
from pymongo import MongoClient

# local
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.abspath(dir_path), '..'))
from bycon.lib.cgi_utils import cgi_parse_query,cgi_print_json_response
from bycon.lib.read_specs import read_local_prefs,read_named_prefs
from bycon.lib.query_generation import geo_query

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

    these_prefs = read_local_prefs( service, dir_path )
    defs = these_prefs["defaults"]

    byc = {
        "config": read_named_prefs( "defaults", dir_path ),
        "form_data": cgi_parse_query(),
        "geoloc_definitions": read_named_prefs( "geoloc_definitions", dir_path ),
        service: these_prefs
    }

    byc["geoloc_definitions"]["geo_root"] = ""
    
    # response prototype
    r = byc[ "config" ]["response_object_schema"]
    r["response_type"] = service

    query, geo_pars = geo_query( **byc )
    for g_k, g_v in geo_pars.items():
        r["parameters"].update( { g_k: g_v })

    if len(query.keys()) < 1:
        r["errors"].append( "No query generated - missing or malformed parameters" )
        cgi_print_json_response( byc[ "form_data" ], r, 422 )

    mongo_client = MongoClient( )
    g_coll = mongo_client[ defs["db"] ][ defs["coll"] ]
    for this in g_coll.find( query, { '_id': False } ):
        r["data"].append( this )
    mongo_client.close( )

    r[service+"_count"] = len(r["data"])

    cgi_print_json_response( byc[ "form_data" ], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
