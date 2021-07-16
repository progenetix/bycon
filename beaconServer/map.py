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

    map()
    
################################################################################

def map():

    byc = initialize_service()
    create_empty_service_response(byc)

    # for e_s_k, e_s in byc["beacon_map"]["endpointSets"].items():
    #     print(e_s["rootUrl"])


    byc.update({"service_response": byc["beacon_map"] })




    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
