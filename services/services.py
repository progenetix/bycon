#!/usr/local/bin/python3

from os import path, pardir
import sys, re, cgitb
from importlib import import_module

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )

bycon_path = path.join( pkg_path, "bycon" )
sys.path.append( bycon_path )

# services that have been moved need to be imported
from info import info
from beacon import beacon
from biosamples import biosamples
from variants import variants
from filteringTerms import filteringTerms

bycon_lib_path = path.join( pkg_path, "bycon", "lib" )
sys.path.append( bycon_lib_path )
from read_specs import read_local_prefs
from cgi_utils import rest_path_value, cgi_print_json_response, set_debug_state

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
    these_prefs = read_local_prefs( "service_mappings", dir_path )

    s_name = path.splitext(path.basename(__file__))[0]

    if path in these_prefs["service_names"]:
        service_name = path
    else:
        service_name = rest_path_value(s_name)

    if service_name in these_prefs["service_names"]:    
        f = these_prefs["service_names"][ service_name ]
        
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

    cgi_print_json_response( {}, { "errors" : [ "No correct service path provided. Please refer to the documentation at http://info.progenetix.org/tags/services" ] }, 422 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
