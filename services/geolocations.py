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
from bycon.lib.cgi_utils import cgi_parse_query,cgi_print_json_response,cgi_break_on_errors
from bycon.lib.read_specs import read_bycon_configs_by_name
from bycon.lib.query_generation import geo_query
from bycon.lib.query_execution import mongo_result_list
from bycon.lib.service_utils import *

"""podmd
* <https://progenetix.org/services/geolocations?city=zurich>
* <https://progenetix.org/services/geolocations?geolongitude=8.55&geolatitude=47.37&geodistance=100000>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    geolocations()
    
################################################################################

def geolocations():

    byc = initialize_service()

    # for the geolocs database, not the provenance object
    byc["geoloc_definitions"]["geo_root"] = "geo_location"
    
    r = create_empty_service_response(byc)

    query, geo_pars = geo_query( **byc )
    for g_k, g_v in geo_pars.items():
        response_add_parameter(r, g_k, g_v)

    if len(query.keys()) < 1:
        response_add_error(r, 422, "No query generated - missing or malformed parameters" )
    
    cgi_break_on_errors(r, byc)

    results, e = mongo_result_list( byc["geo_db"], byc["geo_coll"], query, { '_id': False } )
    if e:
        response_add_error(r, 422, e)
    
    cgi_break_on_errors(r, byc)

    populate_service_response( byc, r, results)
    cgi_print_json_response( byc, r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
