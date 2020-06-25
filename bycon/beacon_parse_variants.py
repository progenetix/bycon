import cgi, cgitb
import re, yaml
import logging
import sys
  
################################################################################

def parse_variants( **byc ):

    variant_pars = { }
    v_p_defs = byc["variant_defs"]["parameters"]
    for v_par in v_p_defs:
        v_default = None
        if "default" in v_p_defs[ v_par ]:
            v_default = v_p_defs[ v_par ][ "default" ]
        variant_pars[ v_par ] = byc["form_data"].getvalue(v_par, v_default)
        if not variant_pars[ v_par ]:
            del( variant_pars[ v_par ] )
        try:
            if v_p_defs[ v_par ][ "type" ] == "integer":
                variant_pars[ v_par ] = int( variant_pars[ v_par ] )
        except Exception:
            pass

    # for debugging
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

    # TODO: rest_pars shouldn't be used anymore; still for cytomapper...
    if "rest_pars" in byc:
        for rp in byc[ "rest_pars" ].keys():
            if rp in v_p_defs:
                variant_pars[ rp ] = byc[ "rest_pars" ][ rp ]

    return variant_pars

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
    brts = byc["variant_defs"]["request_types"]
    v_p_defs = byc["variant_defs"]["parameters"]
    vpars = byc["variant_pars"]
    vrt_matches = [ ]

    for vrt in brts.keys():

        matched_par_no = 0
        needed_par_no = 0
        if "one_of" in brts[vrt]:
            needed_par_no = 1
            for one_of in brts[vrt][ "one_of" ]:
                if one_of in vpars:
                    if re.compile( v_p_defs[ one_of ][ "pattern" ] ).match( str( vpars[ one_of ] ) ):
                        needed_par_no = 0
                        continue
        needed_par_no += len( brts[vrt][ "all_of" ] )

        for required in brts[vrt][ "all_of" ]:
            if required in vpars:
                if re.compile( v_p_defs[ required ][ "pattern" ] ).match( str( vpars[ required ] ) ):
                    matched_par_no += 1
        if matched_par_no >= needed_par_no:
            vrt_matches.append( { "type": vrt, "par_no": matched_par_no } )

    if len(vrt_matches) > 0:
        vrt_matches = sorted(vrt_matches, key=lambda k: k['par_no'], reverse=True)
        variant_request_type = vrt_matches[0]["type"]

    return( variant_request_type )

################################################################################

def create_beacon_allele_request_query(variant_request_type, variant_pars):

    """podmd
    beacon_allele_request:
        all_of:
          - start
          - referenceName
          - referenceBases
          - alternateBases
    podmd"""

    if variant_request_type != "beacon_allele_request":
        return

    # TODO: Regexes for ref or alt with wildcard characters

    v_q_p = [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start_min": int(variant_pars[ "start" ]) }
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

    print(variant_query)

    return( variant_query )

################################################################################

def create_beacon_cnv_request_query(variant_request_type, variant_pars):

    if variant_request_type != "beacon_cnv_request":
        return
        
    variant_query = { "$and": [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start_min": { "$lt": int(variant_pars[ "startMax" ]) } },
        { "end_max": { "$gte": int(variant_pars[ "endMin" ]) } },
        { "start_max": { "$gte": int(variant_pars[ "startMin" ]) } },
        { "end_min": { "$lt": int(variant_pars[ "endMax" ]) } },
        { "variant_type": variant_pars[ "variantType" ] }
    ]}

    return( variant_query )

################################################################################

def create_beacon_range_request_query(variant_request_type, variant_pars):

    # TODO

    if variant_request_type != "beacon_range_request":
        return

    v_q_l = [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start_min": { "$lt": int(variant_pars[ "endMax" ]) } },
        { "end_max": { "$gt": int(variant_pars[ "startMin" ]) } }
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

    return( variant_query )

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
