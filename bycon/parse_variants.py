import cgi, cgitb
import re, yaml
import logging
import sys

from .cgi_utils import *

################################################################################

def parse_variants( **byc ):

    variant_pars = { }
    v_p_defs = byc["variant_defs"]["parameters"]

    for p_k in v_p_defs.keys():
        v_default = None
        if "default" in v_p_defs[ p_k ]:
            v_default = v_p_defs[ p_k ][ "default" ]
        if "array" in v_p_defs[ p_k ]["type"]:
            variant_pars[ p_k ] = form_return_listvalue( byc["form_data"], p_k )
        else:
            variant_pars[ p_k ] = byc["form_data"].getvalue(p_k, v_default)
        if not variant_pars[ p_k ]:
            del( variant_pars[ p_k ] )
        # except Exception:
        #     pass

    # for debugging
    if "args" in byc:
        args = byc["args"]
        if "test" in args:
            if args.test:
                variant_pars = byc["service_info"][ "sampleAlleleRequests" ][0]
        if "cytobands" in args:
            if args.cytobands:
                variant_pars[ "cytoBands" ] = args.cytobands
        if "chrobases" in args:
            if args.chrobases:
                variant_pars[ "chroBases" ] = args.chrobases
        if "genome" in args:
            if args.genome:
                variant_pars[ "assemblyId" ] = args.genome

    # value checks
    v_p_c = { }
    for p_k in variant_pars.keys():
        if not p_k in v_p_defs.keys():
            continue
        v_p = variant_pars[ p_k ]
        if "array" in v_p_defs[ p_k ]["type"]:
            v_l = [ ]
            for v in v_p:
                if re.compile( v_p_defs[ p_k ][ "items" ][ "pattern" ] ).match( str( v ) ):
                    if "integer" in v_p_defs[ p_k ][ "items" ][ "type" ]:
                        v = int( v )
                    v_l.append( v )
            v_p_c[ p_k ] = sorted( v_l )
        else:
            if re.compile( v_p_defs[ p_k ][ "pattern" ] ).match( str( v_p ) ):
                if "integer" in v_p_defs[ p_k ][ "type" ]:
                    v_p = int( v_p )
                v_p_c[ p_k ] = v_p

    # TODO: this is meant to accommodate the "<end" interbase matches; 
    # should probably be more systematic
    for k in [ "start", "end" ]:
        if k in v_p_c:
            if len(v_p_c[ k ]) == 1:
                v_p_c[ k ].append( v_p_c[ k ][0] + 1 )

    return v_p_c

################################################################################

def get_variant_request_type( **byc ):
    """podmd
    This method guesses the type of variant request, based on the complete
    fulfillment of the required parameters (all of `all_of`, at least one of
    `one_of`).
    In case of multiple types the one with most matched parameters is prefered.
    This may be changed to using a pre-defined request type and using this as
    completeness check only.
    podmd"""

    variant_request_type = "no correct variant request"

    v_pars = byc["variant_pars"]
    v_p_defs = byc["variant_defs"]["parameters"]
    g_v_defs = byc["variant_defs"]["BeaconRequestTypes"]["g_variant"]

    # TODO: The first test here is for the hard-coded g_variants types which
    # are still pretty much in testing...
    rts = byc["form_data"].getvalue("requestType")

    if rts in g_v_defs.keys():
        brts = g_v_defs
        brts_k = [ rts ]
    else:
        brts = byc["variant_defs"]["request_types"]
        brts_k = brts.keys()
        # HACK: setting to range request to override possible CNV match
        # i.e. if precise, single start and end values are provided without
        # explicit requestType => a range query w/ any overlap is assumed
        if "start" in v_pars:
            if v_pars[ "start" ][1] == v_pars[ "start" ][0] + 1:
                if v_pars[ "end" ][1] == v_pars[ "end" ][0] + 1:
                    if "referenceName" in v_pars:
                        if "assemblyId" in v_pars:
                            brts_k = [ "variantRangeRequest" ]

    vrt_matches = [ ]

    for vrt in brts_k:
        matched_par_no = 0
        needed_par_no = 0
        if "one_of" in brts[vrt]:
            needed_par_no = 1
            for one_of in brts[vrt][ "one_of" ]:
                if one_of in v_pars:
                    needed_par_no = 0
                    continue
        needed_par_no += len( brts[vrt][ "all_of" ] )

        for required in brts[vrt][ "all_of" ]:
            if required in v_pars:
                matched_par_no += 1
            # print("{} {} of {}".format(vrt, matched_par_no, needed_par_no))

        if matched_par_no >= needed_par_no:
            vrt_matches.append( { "type": vrt, "par_no": matched_par_no } )

    if len(vrt_matches) > 0:
        vrt_matches = sorted(vrt_matches, key=lambda k: k['par_no'], reverse=True)
        variant_request_type = vrt_matches[0]["type"]

    return variant_request_type

################################################################################

def create_variantAlleleRequest_query(variant_request_type, variant_pars):

    """podmd
 
    podmd"""

    if variant_request_type != "variantAlleleRequest":
        return

    # TODO: Regexes for ref or alt with wildcard characters

    v_q_p = [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start_min": int(variant_pars[ "start" ][0]) }
    ]
    for p in [ "referenceBases", "alternateBases" ]:
        if not variant_pars[ p ] == "N":
            p_n = p.replace("Bases", "_bases")
            if "N" in variant_pars[ p ]:
                rb = variant_pars[ p ].replace("N", ".")
                v_q_p.append( { p_n: { '$regex': rb } } )
            else:
                 v_q_p.append( { p_n: variant_pars[ p ] } )
        
    variant_query = { "$and": v_q_p}

    return( variant_query )

################################################################################

def create_variantCNVrequest_query(variant_request_type, variant_pars):

    if not variant_request_type in [ "variantCNVrequest" ]:
        return

    variant_query = { "$and": [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start_min": { "$lt": variant_pars[ "start" ][-1] } },
        { "end_max": { "$gte": variant_pars[ "end" ][0] } },
        { "start_max": { "$gte": variant_pars[ "start" ][0] } },
        { "end_min": { "$lt": variant_pars[ "end" ][-1] } },
        { "variant_type": variant_pars[ "variantType" ] }
    ]}

    return( variant_query )

################################################################################

def create_variantRangeRequest_query(variant_request_type, variant_pars):

    # TODO
    if variant_request_type != "variantRangeRequest":
        return

    v_q_l = [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start_min": { "$lt": int(variant_pars[ "end" ][-1]) } },
        { "end_max": { "$gt": int(variant_pars[ "start" ][0]) } }
    ]

    if "variantType" in variant_pars:
        v_q_l.append( { "variant_type": variant_pars[ "variantType" ] } )
    elif "alternateBases" in variant_pars:
        # the N wildcard stands for any length alt bases so can be ignored
        if not variant_pars[ "alternateBases" ] == "N":
            v_q_l.append( { "alternate_bases": variant_pars[ "alternateBases" ] } )
    else:
        return

    variant_query = { "$and": v_q_l }

    return variant_query

################################################################################

def create_query_from_variant_pars(**byc):
        
    queries = { }
    query_lists = { }
    for coll_name in byc[ "config" ][ "collections" ]:
        query_lists[coll_name] = [ ]
 
    for filterv in byc[ "filters" ]:
        pref = re.split('-|:', filterv)[0]
        
        if pref in byc["filter_defs"]:
            pref_defs = byc["filter_defs"][pref]
            if re.compile( pref_defs["pattern"] ).match(filterv):
                for scope in pref_defs["scopes"]:
                    m_scope = pref_defs["scopes"][scope]
                    if m_scope["default"]:
                        query_lists[ scope ].append( { pref_defs[ "db_key" ]: { "$regex": "^"+filterv } } )

    for coll_name in byc[ "config" ][ "collections" ]:
        if len(query_lists[coll_name]) == 1:
            queries[ coll_name ] = query_lists[coll_name][0]
        elif len(query_lists[coll_name]) > 1:
            queries[ coll_name ] = { "$and": query_lists[coll_name] }
        
    return queries

################################################################################
