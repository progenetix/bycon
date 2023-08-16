#!/usr/bin/env python3

import sys, re
from deepmerge import always_merger
from os import path, pardir
from importlib import import_module

from bycon import *

"""
"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        beacon()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)

################################################################################

def beacon():

    set_debug_state(debug=0)

    b_m_f = path.join(pkg_path, "config", "beacon_mappings.yaml")
    b_m = load_yaml_empty_fallback(b_m_f)
    s_m_f = path.join(pkg_path, "config", "services_mappings.yaml")
    s_m = load_yaml_empty_fallback(s_m_f)
    b_m = always_merger.merge(s_m, b_m)
    byc.update({"beacon_mappings": b_m})

    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    if mod is not None:
        sub_path = path.dirname( path.abspath(mod.__file__) )
        conf_dir = path.join( sub_path, "local" )
        if path.isdir(conf_dir):
            b_m_f = path.join(conf_dir, "beacon_mappings.yaml")
            b_m = load_yaml_empty_fallback(b_m_f)
            s_m_f = path.join(conf_dir, "services_mappings.yaml")
            s_m = load_yaml_empty_fallback(s_m_f)
            b_m = always_merger.merge(s_m, b_m)
            d_f = Path( path.join( conf_dir, "beacon_defaults.yaml" ) )

            if path.isfile(d_f):
                byc.update({"beacon_defaults": load_yaml_empty_fallback( d_f ) })
                defaults = byc["beacon_defaults"].get("defaults", {})
                for d_k, d_v in defaults.items():
                    byc.update( { d_k: d_v } )
            read_bycon_definition_files(conf_dir, byc)
            byc.update({"beacon_mappings": always_merger.merge(byc["beacon_mappings"], b_m)})

    s_a_s = byc["beacon_mappings"].get("service_aliases", {})
    r_w = byc["beacon_mappings"].get("rewrites", {})

    """
    The type of execution depends on the requested entity defined in `beacon_mappings`
    which can either be one of the Beacon entities (also recognizing aliases)
    in `beacon_mappings.service_aliases` or targets of a rewrite from
    `beacon_mappings.rewrites`.
    The entity is determined from different potential inputs and overwritten
    by the next one in the oreder, if existing:

    1. from the path (element after "beacon", e.g. `biosamples` from
       `/beacon/biosamples/...`)
    2. from a form value, e.g. `?requestEntityPathId=biosamples`
    3. from a command line argument, e.g. `--requestEntityPathId biosamples`

    Fallback is `/info`.
    """
    byc.update({"request_path_root": "beacon"})
    rest_path_elements(byc)
    get_bycon_args(byc)
    args_update_form(byc)
    e_p_id = byc["form_data"].get("request_entity_path_id", "___none___")
    if e_p_id in s_a_s or e_p_id in r_w:
        byc.update({"request_entity_path_id": e_p_id})

    r_p_id = byc.get("request_entity_path_id", "info")

    # check for rewrites
    if r_p_id in r_w:
        uri = environ.get('REQUEST_URI')
        pat = re.compile( rf"^.+\/{r_p_id}\/?(.*?)$" )
        if pat.match(uri):
            stuff = pat.match(uri).group(1)
            print_uri_rewrite_response(r_w[r_p_id], stuff)

    f = s_a_s.get(r_p_id)
    if not f:
        pass
    elif f in b_m["data_pipeline_entry_types"]:
        beacon_data_pipeline(byc, f)
    elif f:
        # dynamic package/function loading; e.g. `filteringTerms` loads
        # `filteringTerms` from `filteringTerm.py` which is an alias to
        # the `filtering_terms` function there...
        try:
            mod = import_module(f)
            serv = getattr(mod, f)
            serv()
            exit()
        except Exception as e:
            print('Content-Type: text')
            print('status:422')
            print()
            print('Service {} WTF error: {}'.format(f, e))

            exit()

    byc.update({
        "service_response": {},
        "error_response": {
            "error": {
                "error_code": 422,
                "error_message": "No correct service path provided. Please refer to the documentation at http://docs.progenetix.org"
            }
        }
    })

    cgi_print_response(byc, 422)
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
