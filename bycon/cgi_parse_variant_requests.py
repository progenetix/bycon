import cgi, cgitb
import re, yaml
from os import path as path
  
################################################################################

def read_variant_definitions(**kwargs):

    variant_defs = {}
    with open( path.join(path.abspath(kwargs[ "config" ][ "paths" ][ "mod_root" ]), "config", "variant_parameters.yaml") ) as vd:
        v_defs = yaml.load( vd , Loader=yaml.FullLoader)
        variant_defs = v_defs["parameters"]     
    
    variant_request_types = {}
    with open( path.join(path.abspath(kwargs[ "config" ][ "paths" ][ "mod_root" ]), "config", "variant_request_types.yaml") ) as vrt:
        v_reqs = yaml.load( vrt , Loader=yaml.FullLoader)
        variant_request_types = v_reqs["parameters"]
    
    return( variant_defs, variant_request_types )

################################################################################

def parse_variants(form_data, variant_defs):

    variant_pars = { }
    for v_par in variant_defs:    
        if v_par in form_data.keys():
            variant_pars[ v_par ] = form_data.getvalue(v_par)
    
    return( variant_pars )

################################################################################

def get_variant_request_type(variant_defs, variant_pars, variant_request_types):

    variant_request_type = "no variant request"
    vrt_matches = [ ]

    for vrt in variant_request_types:
        matched_pars = [ ]
        for required in variant_request_types[ vrt ][ "all_of" ]:
            if required in variant_pars.keys():
                if re.compile( variant_defs[ required ][ "pattern" ] ).match( variant_pars[ required ] ):
                    matched_pars.append( required )
            if len( matched_pars ) >= len( variant_request_types[ vrt ][ "all_of" ] ):
                vrt_matches.append( vrt )
#                 print(vrt+" matched: "+str(matched_pars))

    if len(vrt_matches) == 1:
        variant_request_type = vrt_matches[0]
    elif len(vrt_matches) > 1:
        variant_request_type = "more than one variant request type"

    return( variant_request_type )
    
################################################################################

def create_beacon_cnv_request_query(variant_request_type, variant_pars):

    if variant_request_type != "beacon_cnv_request":
        return
        
    variant_query = { "$and": [
        { "reference_name": variant_pars[ "referenceName" ] },
        { "variant_type": variant_pars[ "variantType" ] },
        { "start": { "$gte": int(variant_pars[ "startMin" ]) } },
        { "start": { "$gte": int(variant_pars[ "startMax" ]) } },
        { "end": { "$gte": int(variant_pars[ "endMin" ]) } },
        { "end": { "$gte": int(variant_pars[ "endMax" ]) } }
    ]}

    return( variant_query )

################################################################################
def create_query_from_variant_pars(**kwargs):
        
    queries = { }
    query_lists = { }
    for coll_name in kwargs[ "config" ][ "collections" ]:
        query_lists[coll_name] = [ ]
 
    for filterv in kwargs[ "filters" ]:
        pref = re.split('-|:', filterv)[0]
        
        if pref in kwargs["filter_defs"]:
            if re.compile( kwargs["filter_defs"][pref]["pattern"] ).match(filterv):
                for scope in kwargs["filter_defs"][pref]["scopes"]:
                    m_scope = kwargs["filter_defs"][pref]["scopes"][scope]
                    if m_scope["default"]:
                        query_lists[ scope ].append( { m_scope[ "db_key" ]: { "$regex": "^"+filterv } } )

    for coll_name in kwargs[ "config" ][ "collections" ]:
        if len(query_lists[coll_name]) == 1:
            queries[ coll_name ] = query_lists[coll_name][0]
        elif len(query_lists[coll_name]) > 1:
            queries[ coll_name ] = { "$and": query_lists[coll_name] }
        
    return queries

################################################################################