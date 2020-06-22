import cgi, cgitb
import re, yaml
from os import path as path
import sys

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.abspath(dir_path))

import beacon_parse_variants

################################################################################

def update_queries_from_filters( **byc ):

    """podmd

    #### `update_queries_from_filters`

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
        
    queries = byc["queries"]
    query_lists = { }
    for c_n in byc[ "config" ][ "collections" ]:
        query_lists[c_n] = [ ]
        if c_n in queries:
            query_lists[c_n].append( queries[c_n] )
 
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

    for c_n in byc[ "config" ][ "collections" ]:
        if len(query_lists[c_n]) == 1:
            queries[ c_n ] = query_lists[c_n][0]
        elif len( query_lists[c_n] ) > 1:
            if "mongostring" in byc:
                queries[ c_n ] = '{ $and: [ '+','.join(query_lists[c_n])+' ] }'
            else:
                queries[ c_n ] = { "$and": query_lists[c_n] }

    return queries

################################################################################

def update_queries_from_endpoints( **byc ):

    queries = byc["queries"]

    if len(byc["endpoint_pars"]) < 1:
        return queries

    for c_n in byc["endpoint_pars"]["queries"].keys():
        epq = byc["endpoint_pars"]["queries"][c_n]
        if c_n in queries:
            queries[c_n] = { '$and': [ epq, queries[c_n] ] }
        else:
            queries[c_n] = epq

    return queries

################################################################################

def inject_id_queries( **byc ):

    # TODO comma-concatenated value split...
    # TODO: make this a general "scoped parameters" function, with config
    # file etc. (see Perl beacon version)

    queries = byc["queries"]
    colls = byc["config"]["collections"]
    for c in colls:
        k = "id"
        if c == "variants":
            k = "digest"
        p = c+".id"
        p_vals = byc["form_data"].getlist(p)
        p_q = { }
        if p_vals:
            if len(p_vals) > 1:
                p_q = { k: { '$in': p_vals } }
            else:
                p_q = { k: p_vals[0] }

            if c in queries:
                queries[c] = { '$and': [ queries[c], p_q ] }
            else:
                queries[c] = p_q

    return queries

################################################################################

def update_variants_query( **byc ):

    queries = byc["queries"]
    c_n = "variants"

    if not byc["variant_request_type"] in byc["variant_defs"]["request_types"].keys():
        if not c_n in queries:
            return queries

    query_lists = { c_n: [ ] }
    if c_n in queries:
        query_lists[c_n].append( queries[c_n] )

    v_q_method = "create_"+byc["variant_request_type"]+"_query"
    v_q = getattr( beacon_parse_variants, v_q_method )( byc["variant_request_type"], byc["variant_pars"] )

    if len(query_lists[c_n]) > 0:
        v_q = { '$and': query_lists[c_n].append(v_q) }

    queries.update( { c_n: v_q })

    return queries

