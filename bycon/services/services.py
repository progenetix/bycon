#!/usr/local/bin/python3

from os import path, pardir, environ
import sys, re, cgitb
from importlib import import_module

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""
The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration for creation of canonical URLs.
"""

################################################################################
################################################################################
################################################################################

def main():

    services()
    
################################################################################

def services():

    set_debug_state(debug=0)
    byc.update({"request_path_root": "services"})
    rest_path_elements(byc)

    m_f = path.join( pkg_path, "config", "services_mappings.yaml")
    b_m = load_yaml_empty_fallback( m_f )

    r_p_id = byc.get("request_entity_path_id", "__empty_value__")

    if r_p_id in b_m["service_aliases"]:    
        f = b_m["service_aliases"][ r_p_id ]
        
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
            print('Service {} error: {}'.format(f, e))

            exit()

    if r_p_id in b_m["rewrites"]:
        uri = environ.get('REQUEST_URI')
        pat = re.compile( rf"^.+\/{r_p_id}\/?(.*?)$" )
        if pat.match(uri):
            stuff = pat.match(uri).group(1)
            print_uri_rewrite_response(b_m["rewrites"][r_p_id], stuff)

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
