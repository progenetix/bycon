#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, path, pardir
import sys, datetime, argparse
from pymongo import MongoClient
from operator import itemgetter

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import *
from bycon.lib.parse_filters import *
from bycon.lib.read_specs import *
from bycon.lib.query_generation import geo_query, create_and_or_query_for_list
from lib.service_utils import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    publications()
    
################################################################################

def publications():

    byc = initialize_service()

    get_filter_flags(byc)
    parse_filters(byc)

    r = create_empty_service_response(byc)

    # data retrieval & response population
    query, e = _create_filters_query( **byc )
    if len(e) > 1:
        response_add_error(r, 422, e )

    geo_q, geo_pars = geo_query( **byc )

    if geo_q:
        for g_k, g_v in geo_pars.items():
            response_add_parameter(r, g_k, g_v)
        if len(query.keys()) < 1:
            query = geo_q
        else:
            query = { '$and': [ geo_q, query ] }

    if len(query.keys()) < 1:
        response_add_error(r, 422, "No query could be constructed from the parameters provided." )

    cgi_break_on_errors(r, byc)

    mongo_client = MongoClient( )
    pub_db = byc["config"]["info_db"]
    pub_coll = mongo_client[ pub_db ][ "publications" ]

    p_re = re.compile( byc["filter_definitions"]["PMID"]["pattern"] )

    p_l = [ ]
    d_k = response_set_delivery_keys(byc)
    
    for pub in pub_coll.find( query, { "_id": 0 } ):
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
 
    results = sorted(p_l, key=itemgetter('sortid'), reverse = True)

    populate_service_response( byc, r, results)
    cgi_print_json_response( byc, r, 200 )

################################################################################
################################################################################

def _create_filters_query( **byc ):

    query = { }
    error = ""

    q_list = [ ]
    count_pat = re.compile( r'^(\w+?)\:([>=<])(\d+?)$' )

    for f in byc[ "filters" ]:
        pre_code = re.split('-|:', f)
        pre = pre_code[0]
        if count_pat.match( f ):
            pre, op, no = count_pat.match(f).group(1,2,3)
            dbk = byc[ "filter_definitions" ][ pre ][ "db_key" ]
            if op == ">":
                op = '$gt'
            elif op == "<":
                op = '$lt'
            elif op == "=":
                op = '$eq'
            else:
                error = "uncaught filter error: {}".format(f)
                continue
            q_list.append( { dbk: { op: int(no) } } )
        elif "start" in byc[ "filter_flags" ][ "precision" ] or len(pre_code) == 1:
            """podmd
            If there was only prefix a regex match is enforced - basically here
            for the selection of PMID labeled publications.
            podmd"""
            q_list.append( { "id": re.compile(r'^'+f ) } )
        else:
            q_list.append( { "id": f } )            

    query = create_and_or_query_for_list('$and', q_list)

    return query, error

################################################################################
################################################################################

if __name__ == '__main__':
    main()
