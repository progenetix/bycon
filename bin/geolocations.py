#!/usr/local/bin/python3

import cgi, cgitb
import re, json
import sys, os
from pymongo import MongoClient

# local
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.abspath(dir_path), '..'))
from bycon.cgi_utils import *
from bycon.beacon_process_specs import *
from bycon.geoquery import *

"""podmd
* <https://progenetix.org/services/geolocations?city=zurich>
* <https://progenetix.org/services/geolocations?geolongitude=-0.13&geolatitude=51.51&geodistance=100000>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    geolocations("geolocations")
    
################################################################################

def geolocations(service):

    config = read_bycon_config( os.path.abspath( dir_path ) )
    these_prefs = read_named_prefs( service, dir_path )
    form_data = cgi_parse_query()
    defs = these_prefs["defaults"]

    byc = {
        "form_data": form_data,
        service: these_prefs
    }
    
    # response prototype
    r = config["response_object_schema"]
    r["response_type"] = service

    query = { }
    if "city" in form_data:
        city = form_data.getvalue("city")
        r["parameters"].update( { "city": city })
        query = { "city": re.compile( r'^'+city, re.IGNORECASE ) }
    else:
        query, geo_pars = geo_query( "geojson", **byc )
        for g_k, g_v in geo_pars.items():
            r["parameters"].update( { g_k: g_v })      

    if len(query.keys()) < 1:
        r["errors"].append( "No query generated - missing or malformed parameters" )
        cgi_print_json_response( form_data, r )

    mongo_client = MongoClient( )
    g_coll = mongo_client[ defs["db"] ][ defs["coll"] ]
    for this in g_coll.find( query, { '_id': False } ):
        r["data"].append( this )
    mongo_client.close( )

    r[service+"_count"] = len(r["data"])

    cgi_print_json_response( form_data, r )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
