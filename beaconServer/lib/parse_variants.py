import cgi, cgitb
import re, yaml
import logging
import sys
from bson.objectid import ObjectId

from cgi_utils import *
from query_execution import mongo_result_list

################################################################################

def parse_variants(byc):

    variant_pars = { }
    v_p_defs = byc["variant_definitions"]["parameters"]

    for p_k in v_p_defs.keys():
        v_default = None
        if "default" in v_p_defs[ p_k ]:
            v_default = v_p_defs[ p_k ][ "default" ]
        variant_pars[ p_k ] = v_default
        if p_k in byc["form_data"]:
            variant_pars[ p_k ] = byc["form_data"][p_k]

        if variant_pars[ p_k ] is None:
            variant_pars.pop(p_k)

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

    byc.update( { "variant_pars": v_p_c } )

    return byc

################################################################################

def get_variant_request_type(byc):
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
    v_p_defs = byc["variant_definitions"]["parameters"]

    brts = byc["variant_definitions"]["request_types"]
    brts_k = brts.keys()
    
    # HACK: setting to range request if start and end with one value
    if "start" in v_pars and "end" in v_pars:
        if len(v_pars[ "start" ]) == 1:
            if len(v_pars[ "end" ]) == 1:
                brts_k = [ "variantRangeRequest" ]

    vrt_matches = [ ]

    for vrt in brts_k:
        matched_par_no = 0
        needed_par_no = 0
        if "one_of" in brts[vrt]:
            needed_par_no = 1
            for one_of in brts[vrt][ "one_of" ]:
                if one_of in v_pars:
                    matched_par_no = 1
                    continue
        
        if "all_of" in brts[vrt]:
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

    byc.update( { "variant_request_type": variant_request_type } )

    return byc

################################################################################

def create_variantIdRequest_query( byc ):

    if byc["variant_request_type"] != "variantIdRequest":
        return byc

    # query database for gene and use coordinates to create range query
    vp = byc["variant_pars"]

    if "_id" in vp:
        v_q = { "_id" : ObjectId( vp[ "_id" ] ) }
    elif "id" in vp:
        v_q = { 
            "$or": [
                { "_id" : ObjectId( vp[ "id" ] ) },
                { "id" : vp[ "id" ] }
            ]
        }
    else:
        return byc

    expand_variant_query(v_q, byc)

    return byc

################################################################################

def create_geneVariantRequest_query( byc ):

    if byc["variant_request_type"] != "geneVariantRequest":
        return byc

    # query database for gene and use coordinates to create range query
    vp = byc["variant_pars"]

    query = { "gene_symbol" : vp[ "geneSymbol" ] }

    results, error = mongo_result_list( "progenetix", "genespans", query, { '_id': False } )

    byc["variant_pars"].update( {
        "referenceName": results[0]["reference_name"],
        "start": [ results[0]["start"] ],
        "end": [ results[0]["end"] ]
    } )
    byc.update( {"variant_request_type": "variantRangeRequest"} )

    create_variantRangeRequest_query( byc )

    return byc

################################################################################

def create_variantAlleleRequest_query( byc ):

    """podmd
 
    podmd"""

    if byc["variant_request_type"] != "variantAlleleRequest":
        return byc

    vp = byc["variant_pars"]

    # TODO: Regexes for ref or alt with wildcard characters

    v_q_l = [
        { "reference_name": vp[ "referenceName" ] },
        { "start": int(vp[ "start" ][0]) }
    ]
    for p in [ "referenceBases", "alternateBases" ]:
        if not vp[ p ] == "N":
            p_n = p.replace("Bases", "_bases")
            if "N" in vp[ p ]:
                rb = vp[ p ].replace("N", ".")
                v_q_l.append( { p_n: { '$regex': rb } } )
            else:
                 v_q_l.append( { p_n: vp[ p ] } )
        
    v_q = { "$and": v_q_l }

    expand_variant_query(v_q, byc)

    return byc

################################################################################

def create_variantCNVrequest_query( byc ):

    if not byc["variant_request_type"] in [ "variantCNVrequest" ]:
        return byc

    vp = byc["variant_pars"]

    v_q = { "$and": [
        { "reference_name": vp[ "referenceName" ] },
        { "start": { "$lt": vp[ "start" ][-1] } },
        { "end": { "$gte": vp[ "end" ][0] } },
        { "start": { "$gte": vp[ "start" ][0] } },
        { "end": { "$lt": vp[ "end" ][-1] } },
        create_and_or_query_for_parameter("variantType", "variant_type", "$or", vp)
    ]}

    expand_variant_query(v_q, byc)

    return byc

################################################################################

def create_variantRangeRequest_query( byc ):

    if not byc["variant_request_type"] in [ "variantRangeRequest" ]:
        return byc
    
    vp = byc["variant_pars"]

    v_q_l = [
        { "reference_name": vp[ "referenceName" ] },
        { "start": { "$lt": int(vp[ "end" ][-1]) } },
        { "end": { "$gt": int(vp[ "start" ][0]) } }
    ]

    if "varMinLength" in vp:
        v_q_l.append( { "info.var_length": { "$gte" : vp[ "varMinLength" ] } } )
    if "varMaxLength" in vp:
        v_q_l.append( { "info.var_length": { "$lte" : vp[ "varMaxLength" ] } } )

    if "variantType" in vp:
        v_q_l.append( create_and_or_query_for_parameter("variantType", "variant_type", "$or", vp) )
    elif "alternateBases" in vp:
        # the N wildcard stands for any length alt bases so can be ignored
        if vp[ "alternateBases" ] == "N":
             v_q_l.append( { "alternate_bases": {'$regex': "." } } )
        else:
            v_q_l.append( { "alternate_bases": vp[ "alternateBases" ] } )

    v_q = { "$and": v_q_l }

    # print(v_q)
    # exit()

    expand_variant_query(v_q, byc)

    return byc

################################################################################

def expand_variant_query(variant_query, byc):

    if "variants" in byc["queries"]:
        byc["queries"].update({"variants": { "$and": [ byc["queries"]["variants"], variant_query ] } } )
    else:
        byc["queries"].update( {"variants": variant_query } )

    return byc

################################################################################


def create_and_or_query_for_list(logic, q_list):

    if not isinstance(q_list, list):
        return q_list

    if not q_list:
        return [ ]

    if len(q_list) > 1:
        return { logic: q_list }

    return q_list[0]

################################################################################

def create_and_or_query_for_parameter(par, qpar, logic, q_pars):

    if not isinstance(q_pars[ par ], list):
        return { qpar: q_pars[ par ] }

    try:
        q_pars[ par ][0]
    except IndexError:
        return { }
 
    if len(q_pars[ par ]) > 1:
        v_t_l = [ ]
        for v_t in q_pars[ par ]:
            v_t_l.append( { qpar: v_t } )
        return { logic: v_t_l }

    return { qpar: q_pars[ par ][0] }


################################################################################
