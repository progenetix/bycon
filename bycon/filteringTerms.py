#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from bycon import *


"""podmd

* <https://beacon.progenetix.org/datasets/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    filtering_terms()
    
################################################################################

def filteringTerms():
    
    filtering_terms()

################################################################################

def filtering_terms():

    byc = initialize_service()

    byc.update({"endpoint": "filtering_terms"})

    parse_beacon_schema(byc)
    select_dataset_ids(byc)
    check_dataset_ids(byc)

    update_datasets_from_dbstats(byc)
    
    r = create_empty_service_response(byc)

    results = return_filtering_terms(byc)

    populate_service_response( byc, r, results )
    cgi_print_json_response( byc, r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
