#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import path as path
from os import environ
import sys, os, datetime, argparse
from pymongo import MongoClient
from operator import itemgetter

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon.cgi_utils import *
from bycon.parse_filters import *
from bycon.read_specs import *
from bycon.geoquery import *

"""podmd

* <https://progenetix.org/services/publications/?filters=PMID>
* <http://progenetix.org/cgi/bycon/bin/publications.py?filters=PMID,genomes:>200,arraymap:>1&method=details>
* <http://progenetix.org/cgi/bycon/bin/publications.py?filters=PMID:22824167&filterPrecision=exact&method=details>
* <http://progenetix.org/cgi/bycon/bin/publications.py?geolongitude=8.55&geolatitude=47.37&geodistance=100000>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    publications("publications")
    
################################################################################

def publications(service):

    config = read_bycon_config( path.abspath( dir_path ) )
    these_prefs = read_named_prefs( service, dir_path )

    byc = {
        "config": config,
        "filter_defs": these_prefs["filter_defs"],
        "geolocations": read_named_prefs( "geolocations", dir_path ),
        "form_data": cgi_parse_query(),
        "errors": [ ],
        "warnings": [ ]
    }

    # first pre-population w/ defaults
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    # ... then modification if parameter in request
    if "method" in byc["form_data"]:
        m = byc["form_data"].getvalue("method")
        if m in these_prefs["methods"].keys():
            byc["method"] = m

    # the method keys can be overriden with "deliveryKeys"
    d_k = form_return_listvalue( byc["form_data"], "deliveryKeys" )
    if len(d_k) < 1:
        if not "all" in byc["method"]:
            d_k = these_prefs["methods"][ byc["method"] ]

    byc.update( { "filter_flags": get_filter_flags( **byc ) } )
    byc.update( { "filters": parse_filters( **byc ) } )

    # response prototype
    r = config["response_object_schema"]
    r.update( { "errors": byc["errors"], "warnings": byc["warnings"] } )
    r["response_type"] = service

    # saving the parameters to the response
    for p in ["method", "filters"]:
        r["parameters"].update( { p: byc[ p ] } )

    # data retrieval & response population
    query, error = _create_filters_query( **byc )
    if len(error) > 1:
        r["errors"].append( error )

    geo_q, geo_pars = geo_query( **byc )

    if geo_q:
        for g_k, g_v in geo_pars.items():
            r["parameters"].update( { g_k: g_v })
        if len(query.keys()) < 1:
            query = geo_q
        else:
            query = { '$and': [ geo_q, query ] }

    if len(query.keys()) < 1:
        r["errors"].append( "No query could be constructed from the parameters provided." )
        cgi_print_json_response( byc["form_data"], r, 422 )

    mongo_client = MongoClient( )
    mongo_coll = mongo_client[ config["info_db"] ][ "publications" ]

    p_re = re.compile( byc["filter_defs"]["PMID"]["pattern"] )

    p_l = [ ]
    for pub in mongo_coll.find( query, { "_id": 0 } ):
        s = { }
        if len(d_k) < 1:
            s = pub
        else:
            for k in d_k:
                # TODO: harmless hack
                if k in pub.keys():
                    if k == "counts":
                        s[ k ] = { }
                        for c in pub[ k ]:
                            if pub[ k ][ c ]:
                                try:
                                    s[ k ][ c ] = int(float(pub[ k ][ c ]))
                                except:
                                    s[ k ][ c ] = 0
                            else:
                                s[ k ][ c ] = 0
                    else:
                        s[ k ] = pub[ k ]
                else:
                    s[ k ] = None
        try:
            s_v = p_re.match(s[ "id" ]).group(2)
            s[ "sortid" ] = int(s_v)
        except:
            s[ "sortid" ] = -1

        p_l.append( s )

    mongo_client.close( )
 
    r["data"] = sorted(p_l, key=itemgetter('sortid'), reverse = True)
    r[service+"_count"] = len(r["data"])

    # response
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

def _create_filters_query( **byc ):

    query = { }
    error = ""

    query_list = [ ]
    count_pat = re.compile( r'^(\w+?)\:([>=<])(\d+?)$' )

    for f in byc[ "filters" ]:
        pre_code = re.split('-|:', f)
        pre = pre_code[0]
        if count_pat.match( f ):
            pre, op, no = count_pat.match(f).group(1,2,3)
            dbk = byc[ "filter_defs" ][ pre ][ "db_key" ]
            if op == ">":
                op = '$gt'
            elif op == "<":
                op = '$lt'
            elif op == "=":
                op = '$eq'
            else:
                error = "uncaught filter error: {}".format(f)
                continue
            query_list.append( { dbk: { op: int(no) } } )
        elif "start" in byc[ "filter_flags" ][ "precision" ] or len(pre_code) == 1:
            query_list.append( { "id": re.compile(r'^'+f ) } )
        else:
            query_list.append( { "id": f } )            

    if len(query_list) > 1:
        query = { '$and': query_list }
    else:
        query = query_list[0]

    return query, error

################################################################################
################################################################################

if __name__ == '__main__':
    main()
