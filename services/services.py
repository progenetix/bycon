#!/usr/local/bin/python3

from os import path, pardir, environ
import sys, re, cgitb
from importlib import import_module

# local
services_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( services_path, pardir )
sys.path.append( pkg_path )

# services that have been moved need to be imported

from beaconServer import *

"""
The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration for creation of canonical URLs.
"""

################################################################################
################################################################################
################################################################################

def main():

    services("")
    
################################################################################

def services(service):

    set_debug_state(debug=0)

    uri = environ.get('REQUEST_URI')

    read_local_prefs( "service_mappings", services_path, byc )

    rest_base_name = "services"

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
            print('Service {} error: {}'.format(f, e))

            exit()


    if service_name in byc["this_config"]["rewrites"]:    
        pat = re.compile( rf"^.+\/{service_name}\/?(.*?)$" )
        if pat.match(uri):
            stuff = pat.match(uri).group(1)
            cgi_print_rewrite_response(byc["this_config"]["rewrites"][service_name], stuff)

    cgi_print_response( {
        "service_response": {
            "response" : {
                "error" : {
                    "error_code": 422,
                    "error_message": "No correct service path provided. Please refer to the documentation at http://info.progenetix.org/tags/services"
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
