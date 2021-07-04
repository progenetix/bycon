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

    core()
    
################################################################################

def core():

    byc = initialize_service()
    run_beacon_init_stack(byc)
    run_beacon(byc)
    if "any_of" in byc["service_response"]["response_summary"]:
        byc["service_response"]["response_summary"].pop("any_of")
    if "all_of" in byc["service_response"]["response_summary"]:
        byc["service_response"]["response_summary"].pop("all_of")
    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
