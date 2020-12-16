#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path, scandir
from urllib.parse import urlparse
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import cgi_parse_query,cgi_print_json_response
from bycon.lib.read_specs import read_bycon_configs_by_name,read_local_prefs,dbstats_return_latest

"""podmd

* <>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    schemas("schemas")
    
################################################################################

def schemas(service):

    byc = {
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        "errors": [ ],
        "warnings": [ ]
    }

    s_data = { }
    s_path = path.join( byc["pkg_path"], "byconeer", "config", "schemas" )
    s_files = [ f.path for f in scandir(s_path) if f.is_file() ]
    s_files = [ f for f in s_files if f.endswith(".yaml") ]

    for s_f in s_files:
        with open( s_f ) as s_f_h:
            s = yaml.load( s_f_h , Loader=yaml.FullLoader)
            s_data.update( { s["title"]: s } )

    url_comps = urlparse( environ.get('REQUEST_URI') )
    p_items = re.split(r'\/|\&', url_comps.path)
    i = 0
    f = ""

    for p in p_items:
        if len(p_items) > i:
            i += 1
            if p == "schemas":
                if p_items[ i ] in s_data.keys():    
                    cgi_print_json_response( {}, s_data[ p_items[ i ] ], 200 )
                    exit()

    r = byc[ "config" ]["response_object_schema"]
    r["errors"].append("No correct schema name provided!")
    cgi_print_json_response( {}, r, 422 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
