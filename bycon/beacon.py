#!/usr/local/bin/python3

from os import path, pardir
import sys, re, cgitb
from importlib import import_module

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
bycon_lib_path = path.join( pkg_path, "bycon", "lib" )

sys.path.append( bycon_lib_path )
from read_specs import read_local_prefs
from cgi_utils import rest_path_value, cgi_print_json_response, set_debug_state

"""
"""

################################################################################
################################################################################
################################################################################

def main():

    beacon()
    
################################################################################

def beacon(path=""):

    set_debug_state()
    these_prefs = read_local_prefs( "beacon_services", dir_path )

    if path in these_prefs["service_names"]:
        service_name = path
    else:
        service_name = rest_path_value("beacon")

    if service_name in these_prefs["service_names"]:    
        f = service_name
        
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