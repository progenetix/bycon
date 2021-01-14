#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import cgi_parse_query,cgi_print_json_response
from bycon.lib.read_specs import read_bycon_configs_by_name,read_local_prefs,dbstats_return_latest
from lib.service_utils import *

"""podmd

* <https://progenetix.org/services/dbstats/>
* <http://progenetix.org/cgi/bycon/services/dbstats.py?method=filtering_terms>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    dbstats("dbstats")
    
################################################################################

def dbstats(service):

    byc = {
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        "form_data": cgi_parse_query(),
        "errors": [ ],
        "warnings": [ ]
    }

    # first pre-population w/ defaults
    these_prefs = read_local_prefs( service, dir_path )
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    if "method" in byc["form_data"]:
        m = byc["form_data"].getvalue("method")
        if m in these_prefs["methods"].keys():
            byc["method"] = m
    if "statsNumber" in byc["form_data"]:
        s_n = byc["form_data"].getvalue("statsNumber")
        try:
            s_n = int(s_n)
        except:
            pass
        if type(s_n) == int:
            if s_n > 0:
                byc["stats_number"] = s_n

    # response prototype
    r = create_empty_service_response(**these_prefs)

    results = [ ]
    ds_stats = dbstats_return_latest( byc["stats_number"], **byc )
    for stat in ds_stats:
        db_latest = { }
        for ds_id, ds_vs in stat["datasets"].items():
            dbs = {}
            for k in these_prefs["methods"][ byc["method"] ]:
                dbs.update({k:ds_vs[k]})
            db_latest.update( { ds_id : dbs })
        results.append(db_latest)

    populate_service_response( r, results )
    cgi_print_json_response( byc[ "form_data" ], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
