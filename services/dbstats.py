#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), pardir))
from bycon.lib.cgi_utils import cgi_parse_query,cgi_print_json_response
from bycon.lib.read_specs import read_named_prefs,read_local_prefs,dbstats_return_latest

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

    form_data = cgi_parse_query()

    byc = {
        "config": read_named_prefs( "defaults", dir_path ),
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

    # response prototype
    r = byc[ "config" ]["response_object_schema"]
    r["response_type"] = service
    r["data"] = { }

    ds_stats = dbstats_return_latest( **byc )
    for ds_id, ds_vs in ds_stats["datasets"].items():
        dbs = {}
        for k in these_prefs["methods"][ byc["method"] ]:
            dbs.update({k:ds_vs[k]})
        r["data"].update( { ds_id : dbs })

    cgi_print_json_response( {}, r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
