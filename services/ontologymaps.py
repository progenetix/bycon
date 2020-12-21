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
from bycon.lib.cgi_utils import *
from bycon.lib.parse_filters import *
from bycon.lib.read_specs import *
from byconeer.lib.schemas_parser import *
from lib.service_utils import *

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
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        "errors": [ ],
        "warnings": [ ],
        "form_data": cgi_parse_query()
    }
    for d in ["filter_definitions"]:
        byc.update( { d: read_bycon_configs_by_name( d ) } )

    # print(json.dumps(byc["response"], indent=4, sort_keys=True, default=str)+"\n")

    these_prefs = read_local_prefs( service, dir_path )

    # first pre-population w/ defaults
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    byc.update( { "filters": parse_filters( **byc ) } )
    byc.update( { "filter_flags": get_filter_flags( **byc ) } )

    # response prototype
    r = create_empty_service_response()


    r["meta"]["response_type"] = service

    r["meta"]["parameters"].append( { "filters": byc[ "filters" ] })
    q_list = [ ]
    pre_re = re.compile(r'^(\w+?)([:-].*?)?$')
    for f in byc[ "filters" ]:
        if pre_re.match( f ):
            pre = pre_re.match( f ).group(1)
            if pre in byc["filter_definitions"]:
                f_re = re.compile( byc["filter_definitions"][ pre ]["pattern"] )
                if f_re.match( f ):
                    if "start" in byc[ "filter_flags" ][ "precision" ]:
                        q_list.append( { byc["query_field"]: { "$regex": "^"+f } } )
                    elif f == pre:
                        q_list.append( { byc["query_field"]: { "$regex": "^"+f } } )
                    else:
                        q_list.append( { byc["query_field"]: f } )
    if len(q_list) < 1:
        r["meta"]["errors"].append("No correct filter value provided!")
        cgi_print_json_response( byc["form_data"], r, 422 )

    if len(q_list) > 1:
        query = { '$and': q_list }
    else:
        query = q_list[0]

    r["response"]["results"] = { }

    c_g = [ ]
    u_c_d = { }
    mongo_client = MongoClient( )
    mongo_coll = mongo_client[ byc["config"]["info_db"] ][ byc["config"]["ontologymaps_coll"] ]
    for o in mongo_coll.find( query, { '_id': False } ):
        for c in o["code_group"]:
            pre, code = re.split("[:-]", c["id"])
            if not pre in u_c_d:
                u_c_d.update( { pre: { } } )
            u_c_d[ pre ].update( { c["id"]: { "id": c["id"], "label": c["label"] } } )
        c_g.append( o["code_group"] )

    u_c = { }
    for pre in u_c_d:
        u_c[ pre ] = []
        for k, u in u_c_d[ pre ].items():
            u_c[ pre ].append(u)


            
    mongo_client.close( )

    r["response"]["results"].update( { "code_groups": c_g, "unique_codes": u_c } )

    r[service+"_count"] = len(r["response"]["results"]["code_groups"])
 
    cgi_print_json_response( byc["form_data"], r, 200 )

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
