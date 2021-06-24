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
from beaconServer.lib.cgi_utils import *
from beaconServer.lib.parse_filters import *
from beaconServer.lib.parse_variants import create_and_or_query_for_list
from beaconServer.lib.read_specs import *
from beaconServer.lib.schemas_parser import *
from beaconServer.lib.service_utils import *

"""podmd
* <https://progenetix.org/services/ontologymaps/?filters=NCIT:C3222>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    ontologymaps()
    
################################################################################

def ontologymaps():

    byc = initialize_service()

    parse_filters(byc)
    get_filter_flags(byc)

    create_empty_service_response(byc)    
 
    q_list = [ ]
    pre_re = re.compile(r'^(\w+?)([:-].*?)?$')
    for f in byc[ "filters" ]:
        f_val = f["id"]
        if pre_re.match( f_val ):
            pre = pre_re.match( f_val ).group(1)
            if pre in byc["filter_definitions"]:
                f_re = re.compile( byc["filter_definitions"][ pre ]["pattern"] )
                if f_re.match( f_val ):
                    if "start" in byc[ "filter_flags" ][ "precision" ]:
                        q_list.append( { byc["query_field"]: { "$regex": "^"+f_val } } )
                    elif f == pre:
                        q_list.append( { byc["query_field"]: { "$regex": "^"+f_val } } )
                    else:
                        q_list.append( { byc["query_field"]: f_val } )
    if len(q_list) < 1:
        response_add_error(byc, 422, "No correct filter value provided!" )

    cgi_break_on_errors(byc)

    query = create_and_or_query_for_list('$and', q_list)

    c_g = [ ]
    u_c_d = { }
    mongo_client = MongoClient( )
    mongo_coll = mongo_client[ byc["config"]["info_db"] ][ byc["config"]["ontologymaps_coll"] ]
    for o in mongo_coll.find( query, { '_id': False } ):
        for c in o["code_group"]:
            pre, code = re.split("[:-]", c["id"])
            u_c_d.update( { c["id"]: { "id": c["id"], "label": c["label"] } } )
        c_g.append( o["code_group"] )

    u_c = [ ]
    for k, u in u_c_d.items():
        u_c.append(u)
            
    mongo_client.close( )

    results =  [ { "term_groups": c_g, "unique_terms": u_c } ]

    populate_service_response( byc, results)
    byc["service_response"]["info"]["count"] = len(results[0]["term_groups"])
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

def schema_detyper(parameter):

    if "type" in parameter:
        if "array" in parameter["type"]:
            return [ ]
        elif "object" in parameter["type"]:
            return { }
        return ""

################################################################################
################################################################################

if __name__ == '__main__':
    main()
