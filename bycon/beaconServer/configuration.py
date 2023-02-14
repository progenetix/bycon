#!/usr/bin/env python3

from os import path, pardir
import sys

# local
pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

################################################################################
################################################################################
################################################################################

def main():

    configuration()
    
################################################################################

def configuration():

    initialize_bycon_service(byc)
    r, e = instantiate_response_and_error(byc, "beaconConfigurationResponse")
    response_meta_set_info_defaults(r, byc)

    c_f = path.join( pkg_path, *byc["config"]["default_model_path"], "beaconConfiguration.json")
    c = load_yaml_empty_fallback( c_f )

    r.update( {"response": c } )

    byc.update({"service_response": r, "error_response": e })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
