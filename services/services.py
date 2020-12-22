#!/usr/local/bin/python3

from os import environ, path, pardir
import sys, re, cgitb
from importlib import import_module

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.read_specs import read_local_prefs
from bycon.lib.cgi_utils import rest_path_value

"""
The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration for creation of canonical URLs.
"""

################################################################################
################################################################################
################################################################################

def main():

    these_prefs = read_local_prefs( "services", dir_path )

    if "debug=1" in environ.get('REQUEST_URI'):
        cgitb.enable()
        print('Content-Type: text')
        print()

    service_name = rest_path_value("services")

    if service_name in these_prefs["service_names"]:    
        f = service_name
        
        # dynamic package/function loading
        try:
            mod = import_module(f)
            serv = getattr(mod, f)
            serv(f)
        except Exception as e:
            print('Content-Type: text')
            print('status:422')
            print()
            print('Service {} error: {}'.format(f, e))

            exit()

    print('Content-Type: text')
    print('status:422')
    print()
    print("No correct service path provided. Please refer to the documentation at http://info.progenetix.org/tags/services")
    exit()

################################################################################
################################################################################

if __name__ == '__main__':
    main()
