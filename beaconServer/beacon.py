#!/usr/local/bin/python3

import sys, re, cgitb
from os import path, pardir
from importlib import import_module

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
bycon_lib_path = path.join( pkg_path, "lib" )
sys.path.append( bycon_lib_path )

from read_specs import read_local_prefs
from cgi_parse import rest_path_value, cgi_print_response, set_debug_state

"""
"""

################################################################################
################################################################################
################################################################################

def main():

    beacon()
    
################################################################################

def beacon(path=""):

    set_debug_state(debug=0)
    byc = {}
    read_local_prefs( "beacon_mappings", pkg_path, byc )

    rest_base_name = "beacon"

    if path in byc["this_config"]["service_names"]:
        service_name = path
    else:
        service_name = rest_path_value(rest_base_name)

    if service_name in byc["this_config"]["service_names"]:    
        f = byc["this_config"]["service_names"][ service_name ]

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

    cgi_print_response( {
        "service_response": {
            "response" : {
                "error" : {
                    "error_code": 422,
                    "error_message": "No correct service path provided. Please refer to the documentation at http://info.progenetix.org/tags/Beacon"
                    },
                }
            }
        },
        422
    )
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
