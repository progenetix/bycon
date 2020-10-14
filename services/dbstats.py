#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import path as path
from os import environ
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon.cgi_utils import *
from bycon.read_specs import *

"""podmd

* <https://progenetix.org/services/dbstats/?filters=NCIT>
* <http://progenetix.org/cgi/bycon/bin/dbstats.py?method=filtering_terms>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    dbstats("dbstats")
    
################################################################################

def dbstats(service):

    config = read_bycon_config( path.abspath( dir_path ) )
    these_prefs = read_named_prefs( service, dir_path )
    form_data = cgi_parse_query()

    byc = {
        "config": config,
        "form_data": cgi_parse_query(),
        "errors": [ ],
        "warnings": [ ]
    }

    # first pre-population w/ defaults
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    if "method" in byc["form_data"]:
        m = byc["form_data"].getvalue("method")
        if m in these_prefs["methods"].keys():
            byc["method"] = m

    # response prototype
    r = config["response_object_schema"]
    r["response_type"] = service
    r["data"] = { }

    ds_stats = dbstats_return_latest( **byc["config"] )
    for ds_id, ds_vs in ds_stats["datasets"].items():
        dbs = {}
        for k in these_prefs["methods"][ byc["method"] ]:
            dbs.update({k:ds_vs[k]})
        r["data"].update( { ds_id : dbs })

    # response prototype
    r = config["response_object_schema"]

    cgi_print_json_response( {}, r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
