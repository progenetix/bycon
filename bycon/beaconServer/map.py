#!/usr/bin/env python3

from os import path, pardir
import sys

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    map()
    
################################################################################

def map():

    r, e = instantiate_response_and_error(byc, "beaconMapResponse")
    response_meta_set_info_defaults(r, byc)

    m_f = path.join( pkg_path, *byc["config"]["default_model_path"], "beaconMap.json")
    beaconMap = load_yaml_empty_fallback( m_f )

    r.update( {"response": beaconMap } )
    byc.update({"service_response": r, "error_response": e })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
