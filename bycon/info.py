#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from bycon.lib.cgi_utils import cgi_print_json_response
from bycon.lib.read_specs import datasets_update_latest_stats
from bycon.lib.schemas_parser import *
from bycon.lib.service_utils import create_empty_service_response,initialize_service,populate_service_response

"""podmd

* <https://progenetix.org/beacon/info/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    info()
    
################################################################################

def info():

    byc = initialize_service()

    parse_beacon_schema(byc)

    r = create_empty_service_response(byc)

    byc["beacon_info"].update({"datasets": datasets_update_latest_stats(byc) })

    populate_service_response( byc, r, [ byc["beacon_info"] ] )
    cgi_print_json_response( byc, r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
