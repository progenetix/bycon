#!/usr/bin/env python3

from os import path, pardir
import sys

# local
pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

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

    r, e = instantiate_response_and_error(byc, "beaconEntryTypesResponse")
    response_meta_set_info_defaults(r, byc)

    e_f = path.join( pkg_path, *byc["config"]["default_model_path"], "beaconConfiguration.json")
    e_t_s = load_yaml_empty_fallback( e_f )

    r["response"].update( {"entry_types": e_t_s["entryTypes"] } )

    byc.update({"service_response": r, "error_response": e })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
