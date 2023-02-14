#!/usr/bin/env python3

import sys, re, cgitb
from os import path, pardir
from importlib import import_module

# local
# pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
# sys.path.append( pkg_path )
from bycon import *

"""
"""

################################################################################
################################################################################
################################################################################

def main():

    beacon()
    
################################################################################

def beacon():

    set_debug_state(debug=0)

    m_f = path.join( pkg_path, "config", "beacon_mappings.yaml")
    b_m = load_yaml_empty_fallback( m_f )

    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    if mod is not None:
        sub_path = path.dirname( path.abspath(mod.__file__) )
        conf_dir = path.join( sub_path, "local" )
        if path.isdir(conf_dir):
            m_f = path.join( conf_dir, "beacon_mappings.yaml")
            if path.isfile(m_f):
                b_m = load_yaml_empty_fallback( m_f )
            d_f = Path( path.join( conf_dir, "beacon_defaults.yaml" ) )
            if path.isfile(d_f):
                byc.update({"beacon_defaults": load_yaml_empty_fallback( d_f ) })
                defaults = byc["beacon_defaults"].get("defaults", {})
                for d_k, d_v in defaults.items():
                    byc.update( { d_k: d_v } )
            read_bycon_definition_files(conf_dir, byc)

    byc.update({"request_path_root": "beacon"})
    rest_path_elements(byc)
    r_p_id = byc.get("request_entity_path_id", "info")
    
    get_bycon_args(byc)
    args_update_form(byc)

    if byc["args"]:
        if byc["args"].requestEntityPathId is not None:
            r_p_id = byc["args"].requestEntityPathId

    if r_p_id in b_m["service_aliases"]:
        f = b_m["service_aliases"][ r_p_id ]

        # the data pipeline will run & terminate; else other service
        if f in b_m["data_pipeline_entry_types"]:
            beacon_data_pipeline(byc, f)

        # dynamic package/function loading
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
