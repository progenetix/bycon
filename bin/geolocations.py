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

"""podmd
* <https://progenetix.org/services/geolocations?city=zurich>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    geolocations("geolocations")
    
################################################################################

def geolocations(service):

    config = read_bycon_config( os.path.abspath( dir_path ) )
    these_prefs = read_service_prefs( service, dir_path )
    form_data = cgi_parse_query()
    defs = these_prefs["defaults"]
    
    # response prototype
    r = config["response_object_schema"]
    r["data"].update({ service: [ ] })

    if "city" in form_data:
        city = form_data.getvalue("city")
    else:
        # TODO: value check & response
        r["errors"].append("No city value provided!")
        cgi_print_json_response( form_data, r )

    r["parameters"].update( { "city": city })

    # data retrieval & response population
    # TODO: coordinates query
    q_list = [ ]
    for q_f in defs["query_fields"]:
        q_list.append( { q_f: re.compile( r'^'+city, re.IGNORECASE ) } )
    if len(q_list) > 1:
        query = { '$and': q_list }
    else:
        query = q_list[0]

    mongo_client = MongoClient( )
    g_coll = mongo_client[ defs["db"] ][ defs["coll"] ]
    for this in g_coll.find( query, { '_id': False } ):
        r["data"][ service ].append( this )
    mongo_client.close( )
 
    # response
    cgi_print_json_response( form_data, r )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
