import cgi, cgitb
import re, yaml
from os import path as path
from pymongo import MongoClient
import sys

from .parse_variants import *
from .geoquery import *

################################################################################

def create_queries( **byc ):

    q_s = { }
    q_s = update_queries_from_filters( q_s, **byc )
    q_s = update_queries_from_hoid( q_s, **byc)
    q_s = update_queries_from_variants( q_s, **byc )
    q_s = update_queries_from_endpoints( q_s, **byc )
    q_s = update_queries_from_geoquery( q_s, **byc )
    q_s = purge_empty_queries( q_s, **byc )
    
    return q_s

################################################################################

def purge_empty_queries( q_s, **byc ):

    empties = [ ]
    for k, v in q_s.items():
        if not v:
            empties.append( k )
    for e_k in empties:
        del( q_s[ k ] )

    return q_s

################################################################################

def update_queries_from_hoid( queries, **byc):

    if "accessid" in byc["form_data"]:
        accessid = byc["form_data"].getvalue("accessid")
        ho_client = MongoClient()
        ho_db = ho_client[ byc["config"]["info_db"] ]
        ho_coll = ho_db[ byc["config"][ "handover_coll" ] ]
        h_o = ho_coll.find_one( { "id": accessid } )
        # accessid overrides ... ?
        if h_o:
            t_k = h_o["target_key"]
            t_v = h_o["target_values"]
            c_n = h_o["target_collection"]
            t_db = h_o["source_db"]
            if not t_db == byc["dataset_ids"][0]:
                return queries
            h_o_q = { t_k: { '$in': t_v } }
            if c_n in queries:
                queries.update( { c_n: { '$and': [ h_o_q, queries[ c_n ] ] } } )
            else:
                queries.update( { c_n: h_o_q } )

    return queries

################################################################################

def update_queries_from_filters( queries, **byc ):

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
        
    query_lists = { }

    logic = byc[ "filter_flags" ][ "logic" ]
    precision = byc[ "filter_flags" ][ "precision" ]

    for c_n in byc[ "config" ][ "collections" ]:
        query_lists[c_n] = [ ]
        if c_n in queries:
            query_lists[c_n].append( queries[c_n] )
 
    mongo_client = MongoClient()
    for filterv in byc[ "filters" ]:
        pre_code = re.split('-|:', filterv)
        pre = pre_code[0]
        if pre in byc["filter_defs"]:
            pre_defs = byc["filter_defs"][pre]
            for scope in pre_defs["scopes"]:
                m_scope = pre_defs["scopes"][scope]
                if m_scope["default"]:
                    if "start" in precision or len(pre_code) == 1:
                        if "mongostring" in byc:
                            filterv = re.sub(':', '\:', filterv)
                            filterv = re.sub('-', '\-', filterv)
                            query_lists[ scope ].append( '{ "'+pre_defs[ "db_key" ]+'": { $regex: /^'+filterv+'/ } }' )
                        else:
                            query_lists[ scope ].append( { pre_defs[ "db_key" ]: { "$regex": "^"+filterv } } )
                        break
                    else:
                        # the mongostring option is used by some command line
                        # helpers & probably should be removed / redone
                        if "mongostring" in byc:
                            query_lists[ scope ].append( '{ "'+pre_defs[ "db_key" ]+'": "'+filterv+'" }' )
                        else:
                            q_keys = { filterv: 1 }

                            """podmd
 
                            The Beacon query paradigm assumes a logical 'AND'
                            between different filters. Also, it assumes that a
                            query against a hierarchical term will also retrieve
                            matches to its child terms. These two paradigms are
                            incompatible if the targets don't store all their
                            hierarchies with them.
                            To resolve queries to include all child terms the 
                            current solution is to perform a look up query for
                            the current filter term, in the collation database
                            (e.g. "biosubsets") that has been defined for the
                            filter's prefix, and create an 'OR' query which
                            replaces the single filter value (if more than one
                            term).
                            
                            podmd"""
                            f_re = re.compile( r"\-$" )
                            if not f_re.match(filterv):
                                for ds_id in byc["dataset_ids"]:
                                    mongo_coll = mongo_client[ ds_id ][ byc["filter_defs"][pre]["collation"] ]
                                    try:
                                        f_def = mongo_coll.find_one( { "id": filterv })
                                        if "child_terms" in f_def:
                                            for c in f_def["child_terms"]:
                                                if pre in c:
                                                    # print(c)
                                                    q_keys.update({c:1})
                                    except:
                                        pass

                            if len(q_keys.keys()) == 1:
                                query_lists[ scope ].append( { pre_defs[ "db_key" ]: filterv } )
                            else:
                                f_q_l = [ ]
                                for f_c in q_keys.keys():
                                    f_q_l.append( { pre_defs[ "db_key" ]: f_c } )
                                query_lists[ scope ].append( { '$or': f_q_l } )
                        break
                        
    mongo_client.close()

    for c_n in byc[ "config" ][ "collections" ]:
        if len(query_lists[c_n]) == 1:
            queries[ c_n ] = query_lists[c_n][0]
        elif len( query_lists[c_n] ) > 1:
            if "mongostring" in byc:
                queries[ c_n ] = '{ '+logic+': [ '+','.join(query_lists[c_n])+' ] }'
            else:
                queries[ c_n ] = { logic: query_lists[c_n] }

    return queries

################################################################################

def update_queries_from_endpoints( queries, **byc ):

    if not "endpoint_pars" in byc:
        return queries

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

def update_queries_from_geoquery( queries, **byc ):

    geo_q, geo_pars = geo_query( **byc )

    if not geo_q:
        return queries

    if not "biosamples" in queries:
        queries["biosamples"] = geo_q
    else:
        queries["biosamples"] = { '$and': [ geo_q, queries["biosamples"] ] }

    return queries

################################################################################

def update_queries_from_variants( queries, **byc ):

    c_n = "variants"

    if not byc["variant_request_type"] in byc["variant_defs"]["request_types"].keys():
        if not c_n in queries:
            return queries

    query_lists = { c_n: [ ] }
    if c_n in queries:
        query_lists[c_n].append( queries[c_n] )

    v_q_method = "create_"+byc["variant_request_type"]+"_query"

    if "variantCNVrequest" in byc["variant_request_type"]:
        v_q = create_variantCNVrequest_query( byc["variant_request_type"], byc["variant_pars"] )
    elif "variantAlleleRequest" in byc["variant_request_type"]:
        v_q = create_variantAlleleRequest_query( byc["variant_request_type"], byc["variant_pars"] )
    elif "variantRangeRequest" in byc["variant_request_type"]:
        v_q = create_variantRangeRequest_query( byc["variant_request_type"], byc["variant_pars"] )

    if len(query_lists[c_n]) > 0:
        v_q = { '$and': query_lists[c_n].append(v_q) }

    queries.update( { c_n: v_q })

    return queries

