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
from beaconServer.lib.cgi_utils import cgi_parse_query,cgi_print_response,cgi_break_on_errors
from beaconServer.lib.read_specs import read_bycon_configs_by_name
from beaconServer.lib.query_generation import geo_query
from beaconServer.lib.query_execution import mongo_result_list
from beaconServer.lib.service_utils import *

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
    
    create_empty_service_response(byc)

    query, geo_pars = geo_query( byc )
    for g_k, g_v in geo_pars.items():
        response_add_parameter(byc, g_k, g_v)

    if len(query.keys()) < 1:
        response_add_error(byc, 422, "No query generated - missing or malformed parameters" )
    
    cgi_break_on_errors(byc)

    results, e = mongo_result_list( byc["dataset_ids"][0], byc["geo_coll"], query, { '_id': False } )
    if e:
        response_add_error(byc, 422, e)
    
    cgi_break_on_errors(byc)

    populate_service_response( byc, results)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
