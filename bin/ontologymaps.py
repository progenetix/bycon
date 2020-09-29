#!/usr/local/bin/python3

import cgi, cgitb
import re, json
import sys, os
from pymongo import MongoClient

# local
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.abspath(dir_path), '..'))
from bycon.cgi_utils import *
from bycon.parse_filters import *
from bycon.read_specs import *

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

    config = read_bycon_config( os.path.abspath( dir_path ) )
    these_prefs = read_named_prefs( service, dir_path )

    byc = {
        "config": config,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "errors": [ ],
        "warnings": [ ],
        "form_data": cgi_parse_query()
    }

    # first pre-population w/ defaults
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    byc.update( { "filters": parse_filters( **byc ) } )
    
    # response prototype
    r = config["response_object_schema"]
    r["response_type"] = service

    if len(byc[ "filters" ]) < 1:
        r["errors"].append("No input codes provided!")
        cgi_print_json_response( byc["form_data"], r, 422 )

    r["parameters"].update( { "filters": byc[ "filters" ] })

    # data retrieval & response population
    q_list = [ ]
    for f in byc[ "filters" ]:
        q_list.append( { byc["query_field"]: f } )
    if len(q_list) > 1:
        query = { '$and': q_list }
    else:
        query = q_list[0]

    r["data"] = { }

    c_g = [ ]
    u_c = { }
    mongo_client = MongoClient( )
    mongo_coll = mongo_client[ byc["db"] ][ byc["coll"] ]
    for o in mongo_coll.find( query, { '_id': False } ):
        for c in o["biocharacteristics"]:
            pre, code = re.split("[:-]", c["id"])
            if not pre in u_c:
                u_c.update( { pre: set(  ) } )
            u_c[ pre ].add( c["id"] )
        c_g.append( o["biocharacteristics"] )

    for pre in u_c:
        u_c[ pre ] = list(u_c[ pre ])
            
    mongo_client.close( )

    r["data"].update( { "code_groups": c_g, "unique_codes": u_c } )

    r[service+"_count"] = len(r["data"]["code_groups"])
 
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
