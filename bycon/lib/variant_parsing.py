import re
from bson.objectid import ObjectId

from cgi_parsing import *
from query_execution import mongo_result_list

################################################################################

def parse_variant_parameters(byc):

    if not "variant_definitions" in byc:
        return byc

    variant_pars = { }
    v_p_defs = byc["variant_definitions"]["parameters"]
    v_t_als = byc["variant_definitions"]["variant_state_aliases"]
    v_t_defs = byc["variant_definitions"]["variant_states"]

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
    translate_reference_name(variant_pars, byc)

    for p_k in variant_pars.keys():
        if not p_k in v_p_defs.keys():
            continue
        v_p = variant_pars[ p_k ]
        if "variant_type" in p_k:
            if v_p in v_t_als:
                v_t_k = v_t_als[v_p]
                if "LiteralSequenceExpression" in v_t_k:
                    v_p_c[ p_k ] = None
                else:
                    v_p_c[ p_k ] = { "$in": v_t_defs[v_t_k]["child_terms"] }
        elif "array" in v_p_defs[ p_k ]["type"]:
            v_l = set()
            for v in v_p:
                if re.compile( v_p_defs[ p_k ][ "items" ][ "pattern" ] ).match( str( v ) ):
                    if "integer" in v_p_defs[ p_k ][ "items" ][ "type" ]:
                        v = int( v )
                    v_l.add( v )
            v_p_c[ p_k ] = sorted( list(v_l) )
        else:
            if re.compile( v_p_defs[ p_k ][ "pattern" ] ).match( str( v_p ) ):
                if "integer" in v_p_defs[ p_k ][ "type" ]:
                    v_p = int( v_p )
                v_p_c[ p_k ] = v_p

    byc.update( { "variant_pars": v_p_c } )

    return byc

################################################################################

def translate_reference_name(variant_pars, byc):

    if not "reference_name" in variant_pars:
        return variant_pars

    r_n = variant_pars[ "reference_name" ]
    r_a = byc["variant_definitions"]["refseq_aliases"]

    if not r_n in r_a.keys():
        variant_pars.pop("reference_name")
        return variant_pars

    variant_pars.update({"reference_name": r_a[r_n] })

    return variant_pars

################################################################################

def get_variant_request_type(byc):

    """podmd
    This method guesses the type of variant request, based on the complete
    fulfillment of the required parameters (all of `all_of`, one if `one_of`).
    In case of multiple types the one with most matched parameters is prefered.
    This may be changed to using a pre-defined request type and using this as
    completeness check only.
    podmd"""

    if not "variant_pars" in byc:
        return byc

    variant_request_type = "no correct variant request"

    v_pars = byc["variant_pars"]
    v_p_defs = byc["variant_definitions"]["parameters"]

    brts = byc["variant_definitions"]["request_types"]
    brts_k = brts.keys()
    
    # DODO HACK: setting to range request if start and end with one value
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

def create_variantTypeRequest_query( byc ):

    if byc["variant_request_type"] != "variantTypeRequest":
        return byc

    vp = byc["variant_pars"]
    v_p_defs = byc["variant_definitions"]["parameters"]

    v_q_l = [
        { v_p_defs["variant_type"]["db_key"]: vp[ "variant_type" ] }
    ]

    if "reference_name" in vp:
        v_q_l.append( { v_p_defs["reference_name"]["db_key"]: vp[ "reference_name" ] })

    if len(v_q_l) == 1:
        v_q = v_q_l[0]
    else:     
        v_q = { "$and": v_q_l }

    expand_variant_query(v_q, byc)

    return byc

################################################################################

def create_variantIdRequest_query( byc ):

    if byc["variant_request_type"] != "variantIdRequest":
        return byc

    # query database for gene and use coordinates to create range query
    vp = byc["variant_pars"]
    v_p_defs = byc["variant_definitions"]["parameters"]

    if "_id" in vp:
        v_q = { v_p_defs["_id"]["db_key"] : ObjectId( vp[ "_id" ] ) }
    elif "id" in vp:
        v_q = { 
            "$or": [
                { v_p_defs["_id"]["db_key"] : ObjectId( vp[ "id" ] ) },
                { v_p_defs["id"]["db_key"] : vp[ "id" ] }
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
    v_p_defs = byc["variant_definitions"]["parameters"]


    query = { "symbol" : vp[ "gene_id" ] }

    results, error = mongo_result_list( "progenetix", "genes", query, { '_id': False } )

    # Since this is a pre-processor to the range request
    byc["variant_pars"].update( {
        "reference_name": "refseq:{}".format(results[0]["accession_version"]),
        "start": [ results[0]["start"] ],
        "end": [ results[0]["end"] ]
    } )

    # translate_reference_name(byc["variant_pars"], byc)
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
    v_p_defs = byc["variant_definitions"]["parameters"]

    # TODO: Regexes for ref or alt with wildcard characters

    v_q_l = [
        { v_p_defs["reference_name"]["db_key"]: vp[ "reference_name" ] },
        { v_p_defs["start"]["db_key"]: int(vp[ "start" ][0]) }
    ]
    for p in [ "reference_bases", "alternate_bases" ]:
        if not vp[ p ] == "N":
            if "N" in vp[ p ]:
                rb = vp[ p ].replace("N", ".")
                v_q_l.append( { v_p_defs[p]["db_key"]: { '$regex': rb } } )
            else:
                 v_q_l.append( { v_p_defs[p]["db_key"]: vp[ p ] } )
        
    v_q = { "$and": v_q_l }

    expand_variant_query(v_q, byc)

    return byc

################################################################################

def create_variantCNVrequest_query( byc ):

    if not byc["variant_request_type"] in [ "variantCNVrequest" ]:
        return byc

    vp = byc["variant_pars"]
    v_p_defs = byc["variant_definitions"]["parameters"]

    v_q = { "$and": [
        { v_p_defs["reference_name"]["db_key"]: vp[ "reference_name" ] },
        { v_p_defs["start"]["db_key"]: { "$lt": vp[ "start" ][-1] } },
        { v_p_defs["end"]["db_key"]: { "$gte": vp[ "end" ][0] } },
        { v_p_defs["start"]["db_key"]: { "$gte": vp[ "start" ][0] } },
        { v_p_defs["end"]["db_key"]: { "$lt": vp[ "end" ][-1] } },
        create_in_query_for_parameter("variant_type", v_p_defs["variant_type"]["db_key"], vp)
    ]}

    expand_variant_query(v_q, byc)

    return byc

################################################################################

def create_variantRangeRequest_query( byc ):

    if not byc["variant_request_type"] in [ "variantRangeRequest" ]:
        return byc
    
    vp = byc["variant_pars"]
    v_p_defs = byc["variant_definitions"]["parameters"]

    v_q_l = [
        { v_p_defs["reference_name"]["db_key"]: vp[ "reference_name" ] },
        { v_p_defs["start"]["db_key"]: { "$lt": int(vp[ "end" ][-1]) } },
        { v_p_defs["end"]["db_key"]: { "$gt": int(vp[ "start" ][0]) } }
    ]

    p_n = "variant_min_length"
    if p_n in vp:
        v_q_l.append( { v_p_defs[p_n]["db_key"]: { "$gte" : vp[p_n] } } )
    p_n = "variant_max_length"
    if "variant_max_length" in vp:
        v_q_l.append( { v_p_defs[p_n]["db_key"]: { "$lte" : vp[p_n] } } )

    p_n = "variant_type"
    if p_n in vp:
        v_q_l.append( create_in_query_for_parameter(p_n, v_p_defs[p_n]["db_key"], vp) )
    elif "alternate_bases" in vp:
        # the N wildcard stands for any length alt bases so can be ignored
        if vp[ "alternate_bases" ] == "N":
             v_q_l.append( { v_p_defs["alternate_bases"]["db_key"]: {'$regex': "." } } )
        else:
            v_q_l.append( { v_p_defs["alternate_bases"]["db_key"]: vp[ "alternate_bases" ] } )

    v_q = { "$and": v_q_l }

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
        return {}

    if len(q_list) > 1:
        return { logic: q_list }

    return q_list[0]

################################################################################

def create_in_query_for_parameter(par, qpar, q_pars):

    if not isinstance(q_pars[ par ], list):
        return { qpar: q_pars[ par ] }

    try:
        q_pars[ par ][0]
    except IndexError:
        return { }
 
    if len(q_pars[ par ]) > 1:
        return { qpar: {"$in": q_pars[ par ]} }

    return { qpar: q_pars[ par ][0] }

################################################################################

def variant_create_digest(v, byc):

    v_d = byc["variant_definitions"]

    t = v["variant_state"]["id"]
    t = re.sub(":", "_", t)

    v_i = v["location"]["interval"]
    p = "{}-{}".format(v_i["start"]["value"], v_i["end"]["value"])

    chro = chroname_from_refseqid(v["location"]["sequence_id"], byc)

    return ":".join( [chro, p, t])

################################################################################

def chroname_from_refseqid(refseqid, byc):

    chr_re = re.compile(r'^refseq:NC_0+([^0]\d?)\.\d\d?$')
    chro = chr_re.match(refseqid).group(1)

    return chro

################################################################################
