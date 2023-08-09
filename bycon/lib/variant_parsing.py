import bson.objectid

from cgi_parsing import *

################################################################################

def parse_variants(byc):
    __parse_variant_parameters(byc)
    __get_variant_request_type(byc)


################################################################################

def __parse_variant_parameters(byc):
    v_d = byc["variant_parameters"]
    v_p_defs = v_d["parameters"]
    v_t_defs = byc["variant_type_definitions"]

    variant_pars = { }

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
    __translate_reference_name(variant_pars, byc)

    for p_k in variant_pars.keys():
        if not p_k in v_p_defs.keys():
            continue
        v_p = variant_pars[ p_k ]
        if "variant_type" in p_k:
            v_s = __variant_state_from_variant_par(v_p, byc)
            if v_s is False:
                v_p_c[ p_k ] = None
            else:
                v_s_id = v_s["id"]  # on purpose here leading to error if ill defined
                v_p_c[ p_k ] = { "$in": v_t_defs[v_s_id]["child_terms"] }
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

    byc.update( { "varguments": v_p_c } )


################################################################################

def __get_variant_request_type(byc):

    """podmd
    This method guesses the type of variant request, based on the complete
    fulfillment of the required parameters (all of `all_of`, one if `one_of`).
    In case of multiple types the one with most matched parameters is prefered.
    This may be changed to using a pre-defined request type and using this as
    completeness check only.
    TODO: Verify by schema ...
    TODO: This is all a bit too complex; probbaly better to just do it as a
          stack of dedicated tests and including a "defined to fail" query
          which is only removed after a successfull type match.
    podmd"""

    if not "varguments" in byc:
        return

    variant_request_type = "no correct variant request"

    v_pars = byc["varguments"]
    v_p_defs = byc["variant_parameters"]["parameters"]

    brts = byc["variant_parameters"]["request_types"]
    brts_k = brts.keys()
    
    # Already hard-coding some types here - if conditions are met only
    # the respective types will be evaluated since only this key is used
    if "start" in v_pars and "end" in v_pars:
        if len(v_pars[ "start" ]) == 1 and len(v_pars[ "end" ]) == 1:
            brts_k = [ "variantRangeRequest" ]
        elif len(v_pars[ "start" ]) == 2 and len(v_pars[ "end" ]) == 2:
            brts_k = [ "variantBracketRequest" ]

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
        
        if matched_par_no >= needed_par_no:
            vrt_matches.append( { "type": vrt, "par_no": matched_par_no } )


    if len(vrt_matches) > 0:
        vrt_matches = sorted(vrt_matches, key=lambda k: k['par_no'], reverse=True)
        variant_request_type = vrt_matches[0]["type"]

    byc.update( { "variant_request_type": variant_request_type } )


################################################################################

def __variant_state_from_variant_par(variant_type, byc):
    v_d = byc["variant_parameters"]
    v_t_defs = byc["variant_type_definitions"]

    for k, d in v_t_defs.items():
        for p, v in d.items():
            if v is None:
                continue
            if type(v) is list:
                continue
            if "variant_state" in p:
                v = v.get("id", "___none___")
            if type(v) is not str:
                continue
            if variant_type.lower() == v.lower():
                return d["variant_state"]

    return False


################################################################################

def __translate_reference_name(variant_pars, byc):

    if not "reference_name" in variant_pars:
        return variant_pars

    r_n = variant_pars[ "reference_name" ]
    g_a = byc.get("genome_aliases", {})
    r_a = g_a.get("refseq_aliases", {})

    if not r_n in r_a.keys():
        variant_pars.pop("reference_name")
        return variant_pars

    variant_pars.update({"reference_name": r_a[r_n] })

    return variant_pars


################################################################################
