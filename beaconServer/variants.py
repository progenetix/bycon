#!/usr/local/bin/python3

import cgi, cgitb, sys
from os import path, environ, pardir

from pymongo import MongoClient
from bson.objectid import ObjectId

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

################################################################################
################################################################################
################################################################################

"""
https://progenetix.test/beacon/variants/?filters=NCIT:C7712&output=pgxseg&debug=1
http://progenetix.test/cgi/bycon/beaconServer/variants.py?start=0,120000000&end=123000000,124500000&referenceName=8&variantType=DUP&filters=icdom-81703&debug=1
"""

def main():

    variants()
    
################################################################################

def variants():

    byc = initialize_service()
    run_beacon_init_stack(byc)
    return_filtering_terms_response(byc)
    run_result_sets_beacon(byc)
    export_datatable(byc)
    check_alternative_variant_deliveries(byc)
    query_results_save_handovers(byc)
    check_switch_to_count_response(byc)
    check_switch_to_boolean_response(byc)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
