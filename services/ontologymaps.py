#!/usr/local/bin/python3

import cgi, cgitb
import re, json
from os import path, pardir
import sys
from pymongo import MongoClient

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), pardir))
from bycon.lib.cgi_utils import *
from bycon.lib.parse_filters import *
from bycon.lib.read_specs import *

"""podmd
* <https://progenetix.org/services/ontologymaps/?filters=NCIT:C3222>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    ontologymaps("ontologymaps")
    
################################################################################

def ontologymaps(service):

    byc = {
        "config": read_named_prefs( "defaults", dir_path ),
        "errors": [ ],
        "warnings": [ ],
        "form_data": cgi_parse_query()
    }
    for d in ["filter_definitions"]:
        byc.update( { d: read_named_prefs( d, dir_path ) } )

    these_prefs = read_local_prefs( service, dir_path )

    # first pre-population w/ defaults
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    byc.update( { "filters": parse_filters( **byc ) } )
    byc.update( { "filter_flags": get_filter_flags( **byc ) } )
    
    # response prototype
    r = byc[ "config" ]["response_object_schema"]
    r["response_type"] = service

    if len(byc[ "filters" ]) < 1:
        r["errors"].append("No input codes provided!")
        cgi_print_json_response( byc["form_data"], r, 422 )

    r["parameters"].update( { "filters": byc[ "filters" ] })

    q_list = [ ]
    for f in byc[ "filters" ]:
        if "start" in byc[ "filter_flags" ][ "precision" ]:
            q_list.append( { byc["query_field"]: { "$regex": "^"+f } } )
        else:
            q_list.append( { byc["query_field"]: f } )
    if len(q_list) > 1:
        query = { '$and': q_list }
    else:
        query = q_list[0]

    r["data"] = { }

    c_g = [ ]
    u_c_d = { }
    mongo_client = MongoClient( )
    mongo_coll = mongo_client[ byc["db"] ][ byc["coll"] ]
    for o in mongo_coll.find( query, { '_id': False } ):
        for c in o["biocharacteristics"]:
            pre, code = re.split("[:-]", c["id"])
            if not pre in u_c_d:
                u_c_d.update( { pre: { } } )
            u_c_d[ pre ].update( { c["id"]: { "id": c["id"], "label": c["label"] } } )
        c_g.append( o["biocharacteristics"] )

    u_c = { }
    for pre in u_c_d:
        u_c[ pre ] = []
        for k, u in u_c_d[ pre ].items():
            u_c[ pre ].append(u)

            
    mongo_client.close( )

    r["data"].update( { "code_groups": c_g, "unique_codes": u_c } )

    r[service+"_count"] = len(r["data"]["code_groups"])
 
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
