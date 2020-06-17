import cgi, cgitb
import re, yaml
from os import path as path

from .cgi_parse_variant_requests import *

################################################################################

def create_queries_from_filters( **byc ):

    """podmd

    #### `create_queries_from_filters`

    This method creates a query object (dictionary) with entries for each of the
    standard data collections.

    Filter values are not checked for their correct syntax; this should have
    happened in a pre-parsing step and allows to use the method with non-standard
    values, e.g. to fix erroneous database entries.

    ###### Options

    * `exact_match` creates query items with exact (string) matches, in contrast
    to the standard teatment of query terms as start-anchored partial matches
    * `mongostring` leads to creation of MongoDB compatible query strings
    instead of `pymongo` objects (i.e. the result is to be used in `mongo`
    commands)

    podmd"""
        
    queries = { }
    query_lists = { }
    for coll_name in byc[ "config" ][ "collections" ]:
        query_lists[coll_name] = [ ]
 
    for filterv in byc[ "filters" ]:
        pre = re.split('-|:', filterv)[0]
        if pre in byc["filter_defs"]:
            pre_defs = byc["filter_defs"][pre]
            for scope in pre_defs["scopes"]:
                m_scope = pre_defs["scopes"][scope]
                if m_scope["default"]:
                    if "exact_match" in byc:
                        if "mongostring" in byc:
                            query_lists[ scope ].append( '{ "'+pre_defs[ "db_key" ]+'": "'+filterv+'" }' )
                        else:
                            query_lists[ scope ].append( { pre_defs[ "db_key" ]: filterv } )
                        break
                    else:
                        if "mongostring" in byc:
                            filterv = re.sub(':', '\:', filterv)
                            filterv = re.sub('-', '\-', filterv)
                            query_lists[ scope ].append( '{ "'+pre_defs[ "db_key" ]+'": { $regex: /^'+filterv+'/ } }' )
                        else:
                            query_lists[ scope ].append( { pre_defs[ "db_key" ]: { "$regex": "^"+filterv } } )
                        break

    for coll_name in byc[ "config" ][ "collections" ]:
        if len(query_lists[coll_name]) == 1:
            queries[ coll_name ] = query_lists[coll_name][0]
        elif len(query_lists[coll_name]) > 1:
            if "mongostring" in byc:
                queries[ coll_name ] = '{ $and: [ '+','.join(query_lists[coll_name])+' ] }'
            else:
                queries[ coll_name ] = { "$and": query_lists[coll_name] }

    return queries




