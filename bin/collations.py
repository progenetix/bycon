#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import path as path
from os import environ
import sys, os, datetime, argparse
from pymongo import MongoClient

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    collations()
    
################################################################################

def collations():

    byc = {
        "config": read_bycon_config( path.abspath( dir_path ) ),
        "args": _get_args(),
        "form_data": cgi_parse_query()
    }

    r = { "data": [ ], "error": "" }


    byc.update( { "dataset_ids": ["progenetix", "arraymap"] } )
    byc.update( { "filters": [ ] } )
    byc.update( { "collation": "" } )

    if "filters" in byc["form_data"]:
        fs = byc["form_data"].getlist('filters')
        fs = ','.join(fs)
        fs = fs.split(',')
        for f in fs:
            c = _check_filter(f, **byc)
    elif "args" in byc:
        if byc["args"].filters:
            fs = byc["args"].filters.split(',')
            for f in fs:
                c = _check_filter(f, **byc)

    if c:
        byc.update( { "collation": c } )
        byc["filters"].append( f )

    if len(byc[ "filters" ]) < 1:
        r.update( { "error": "No accepted filter / prefix provided." })
        cgi_print_json_response( r )

    if len(byc[ "filters" ]) > 1:
        r.update( { "error": "Only s single prefix type is supported." })
        cgi_print_json_response( r )

    f = byc["filters"][0]

    mongo_client = MongoClient( )
    query = { "id": re.compile(r'^'+f ) }

    for ds_id in byc["dataset_ids"]:
        mongo_coll = mongo_client[ ds_id ][ byc["collation"] ]
        ds_s = [ ]
        for subset in mongo_coll.find( query ):
            s = { }
            for k in ["id", "label", "count", "child_terms"]:
                s[ k ] = subset[ k ]
            ds_s.append( s )
        r["data"].append( { ds_id: ds_s } )
 
    cgi_print_json_response( r )

################################################################################

def _check_filter(f, **byc):

    f_m = re.compile( r'^(\w+?)([\-\:]\w.+?)?$' )
    pre, code = f_m.match( f ).group(1, 2)
    for c, v in byc["config"]["collations"].items():
        if pre in v["prefixes"]:
            return c

    return False

################################################################################
################################################################################

if __name__ == '__main__':
    main()
