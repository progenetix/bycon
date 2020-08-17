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

* <https://progenetix.org/services/collations/?filters=NCIT>
* <http://progenetix.org/cgi/bycon/bin/collations.py?filters=NCIT&datasetIds=progenetix&method=counts>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    collations()
    
################################################################################

def collations():

    config = read_bycon_config( path.abspath( dir_path ) )
    coll_prefs = read_yaml_to_object( "collations_preference_file", **config[ "paths" ] )

    byc = {
        "config": config,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "form_data": cgi_parse_query()
    }

    for d_k, d_v in coll_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    if "method" in byc["form_data"]:
        m = byc["form_data"].getvalue("method")
        if m in coll_prefs["methods"].keys():
            byc["method"] = m

    method_keys = coll_prefs["methods"][ byc["method"] ]

    if "datasetIds" in byc["form_data"]:
        d_s = byc[ "form_data" ].getlist('datasetIds')
        d_s = ','.join(d_s)
        byc.update( { "dataset_ids": d_s.split(',') } )

    filters = parse_filters( **byc )
    if len(filters) > 0:
        byc.update( { "filters":  filters } )

    # response prototype
    r = {
        "parameters": { },
        "data": [ ],
        "errors": [ ]
    }

    for p in ["dataset_ids", "method", "filters"]:
        r["parameters"].update( { p: byc[ p ] } )

    mongo_client = MongoClient( )

    for ds_id in byc["dataset_ids"]:
        mongo_db = mongo_client[ ds_id ]
        for f in byc[ "filters" ]:
            query = { "id": re.compile(r'^'+f ) }
            pre = re.split('-|:', f)[0]
            c =  byc["filter_defs"][ pre ]["collation"]
            ds_s = [ ]
            mongo_coll = mongo_db[ c ]
            for subset in mongo_coll.find( query ):
                s = { }
                for k in method_keys:
                    # TODO: harmless hack
                    if k == "count":
                        s[ k ] = int(subset[ k ])
                    else:
                        s[ k ] = subset[ k ]
                ds_s.append( s )
            r["data"].append( { ds_id: ds_s } )
 
    cgi_print_json_response( r )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
