#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path, scandir
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib.cgi_utils import cgi_parse_query, cgi_print_response, rest_path_value
from beaconServer.lib.schemas_parser import *
from beaconServer.lib.service_utils import *

"""podmd

* <https://progenetix.org/services/schemas/Biosample>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    schemas()
    
################################################################################

def schemas():

    byc = initialize_service()
    create_empty_service_response(byc)

    s_path = path.join( pkg_path, "schemas" )
    s_files = [ f.name for f in scandir(s_path) if f.is_file() ]
    s_files = [ f for f in s_files if f.endswith(".yaml") ]
    s_files = [ f for f in s_files if not f.startswith("_") ]
    # commenting beacon since remote $ref are not handled yet
    # s_files = [ f for f in s_files if not f.startswith("beacon") ]

    schema_name = rest_path_value("schemas")

    if schema_name is not False:
        for s_f in s_files:
            f_name = os.path.splitext( s_f )[0]
            if f_name == schema_name:
                s = read_schema_files(f_name, "")
                if "$id" in s:
                    byc["service_response"]["meta"]["returned_schemas"] = [ s["$id"] ]
                populate_service_response(byc, [s])
                cgi_print_response( byc, 200 )
                exit()
    
    response_add_error(byc, 422, "No correct schema name provided!")
 
    cgi_print_response( byc, 422 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
