#!/usr/local/bin/python3

import sys, re, cgitb
from os import path, pardir
from importlib import import_module

# local
pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir )
sys.path.append( pkg_path )

from beaconServer import *


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

    rest_base_name = "beacon"

    m_f = path.join( pkg_path, "config", "beacon_mappings.yaml")
    b_m = load_yaml_empty_fallback( m_f )

    # TODO: service names from endpoints.yaml
    service_name = rest_path_value(rest_base_name)

    if service_name in b_m["service_aliases"]:    
        f = b_m["service_aliases"][ service_name ]

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
