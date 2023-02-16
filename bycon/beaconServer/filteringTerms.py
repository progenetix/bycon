#!/usr/bin/env python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""podmd

* <https://beacon.progenetix.org/beacon/filteringTerms

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

    initialize_bycon_service(byc)
    run_beacon_init_stack(byc)
    select_dataset_ids(byc)
    return_filtering_terms_response(byc)

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
