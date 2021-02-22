#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path, scandir
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import cgi_parse_query, cgi_print_json_response, rest_path_value
from byconeer.lib.schemas_parser import *
from lib.service_utils import *

"""podmd

* <https://progenetix.org/services/schemas/Biosample>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    schemas("schemas")
    
################################################################################

def schemas(service):

    byc = initialize_service(service)

    s_data = { }
    s_pkg_path = path.join( byc["pkg_path"], "byconeer")
    s_path = path.join( s_pkg_path, "config", "schemas" )
    s_files = [ f.name for f in scandir(s_path) if f.is_file() ]
    s_files = [ f for f in s_files if f.endswith(".yaml") ]
    s_files = [ f for f in s_files if not f.startswith("_") ]

    for s_f in s_files:
        f_name = os.path.splitext( s_f )[0]
        s_data.update( { f_name: read_schema_files(f_name, "", s_pkg_path) } )

    schema_name = rest_path_value("schemas")
    if schema_name in s_data.keys():    
        cgi_print_json_response( {}, s_data[ schema_name ], 200 )
        exit()

    r = byc[ "config" ]["response_object_schema"]
    response_add_error(r, 422, "No correct schema name provided!")
 
    cgi_print_json_response( {}, r, 422 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
