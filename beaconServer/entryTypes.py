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

    byc = initialize_service()
    # create_empty_service_response(byc)

    create_empty_non_data_response(byc)
    # prjsoncam(byc["service_response"])

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
