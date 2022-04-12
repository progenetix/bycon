#!/usr/local/bin/python3

from os import path, pardir
import sys

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    entry_types()
    
################################################################################

def entryTypes():
    
    entry_types()

################################################################################

def entry_types():

    initialize_service(byc)
    r, e = instantiate_response_and_error(byc, "beaconEntryTypesResponse")
    response_meta_set_info_defaults(r, byc)

    e_f = path.join( pkg_path, "schemas", "src", "progenetix-model", "beaconConfiguration.yaml")
    e_t_s = load_yaml_empty_fallback( e_f )

    r["response"].update( {"entry_types": e_t_s["entryTypes"] } )

    byc.update({"service_response": r, "error_response": e })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
