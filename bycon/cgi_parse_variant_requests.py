import cgi, cgitb
import re, yaml
import logging

from os import path as path
  
################################################################################

def read_variant_definitions(**byc):

    variant_defs = {}
    with open( path.join(path.abspath(byc[ "config" ][ "paths" ][ "module_root" ]), "config", "variant_parameters.yaml") ) as vd:
        v_defs = yaml.load( vd , Loader=yaml.FullLoader)
        variant_defs = v_defs["parameters"]     
    
    variant_request_types = {}
    with open( path.join(path.abspath(byc[ "config" ][ "paths" ][ "module_root" ]), "config", "variant_request_types.yaml") ) as vrt:
        v_reqs = yaml.load( vrt , Loader=yaml.FullLoader)
        variant_request_types = v_reqs["parameters"]
    
    return( variant_defs, variant_request_types )

################################################################################

def parse_variants( **byc ):

    variant_pars = { }
    for v_par in byc[ "variant_defs" ]:
        if v_par in byc[ "form_data" ].keys():
            variant_pars[ v_par ] = byc["form_data"].getvalue(v_par)
        elif "default" in byc[ "variant_defs" ][ v_par ].keys():
            variant_pars[ v_par ] = byc[ "variant_defs" ][ v_par ][ "default" ]

    # for debugging
    for opt, arg in byc["opts"]:
        if opt in ("-t"):
            variant_pars = byc["service_info"][ "sampleAlleleRequests" ][0]
    
    return( variant_pars )

################################################################################

def get_variant_request_type( **byc ):
    """podmd
    This method guesses the type of variant request, based on the complete
    fulfillment of the required parameters (all of `all_of`, at least one of
    `one_of`).
    This may be changed to using a pre-defined request type and using this as
    completeness check only.
    podmd"""

    variant_request_type = "no correct variant request"
    vrt_matches = [ ]

    for vrt in byc[ "variant_request_types" ]:

        matched_par_no = 0
        needed_par_no = 0
        if "one_of" in byc[ "variant_request_types" ][vrt]:
            needed_par_no = 1
            for one_of in byc[ "variant_request_types" ][vrt][ "one_of" ]:
                if one_of in byc["variant_pars"]:
                    if re.compile( byc["variant_defs"][ one_of ][ "pattern" ] ).match( str( byc["variant_pars"][ one_of ] ) ):
                        needed_par_no = 0
                        continue
        needed_par_no += len( byc[ "variant_request_types" ][vrt][ "all_of" ] )

        for required in byc[ "variant_request_types" ][vrt][ "all_of" ]:
            if required in byc["variant_pars"]:
                if re.compile( byc["variant_defs"][ required ][ "pattern" ] ).match( str( byc["variant_pars"][ required ] ) ):
                    matched_par_no += 1
        if matched_par_no >= needed_par_no:
            vrt_matches.append( vrt )

    if len(vrt_matches) == 1:
        variant_request_type = vrt_matches[0]
    elif len(vrt_matches) > 1:
        variant_request_type = "more than one variant request type"

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
        
    variant_query = { "$and": [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start": int(variant_pars[ "start" ]) },
        { "reference_bases": variant_pars[ "referenceBases" ] },
        { "alternate_bases": variant_pars[ "alternateBases" ] }
    ]}

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


    if variant_request_type != "beacon_range_request":
        return

    if "variantType" in variant_pars:
        type_par_q = { "variant_type": variant_pars[ "variantType" ] }
    elif "alternateBases" in variant_pars:
        type_par_q = { "alternate_bases": variant_pars[ "alternateBases" ] }
    else:
        return

    variant_query = { "$and": [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "start": { "$lt": int(variant_pars[ "end" ]) } },
        { "end": { "$gte": int(variant_pars[ "start" ]) } },
        type_par_q
    ]}

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
            if re.compile( byc["filter_defs"][pref]["pattern"] ).match(filterv):
                for scope in byc["filter_defs"][pref]["scopes"]:
                    m_scope = byc["filter_defs"][pref]["scopes"][scope]
                    if m_scope["default"]:
                        query_lists[ scope ].append( { m_scope[ "db_key" ]: { "$regex": "^"+filterv } } )

    for coll_name in byc[ "config" ][ "collections" ]:
        if len(query_lists[coll_name]) == 1:
            queries[ coll_name ] = query_lists[coll_name][0]
        elif len(query_lists[coll_name]) > 1:
            queries[ coll_name ] = { "$and": query_lists[coll_name] }
        
    return queries

################################################################################
