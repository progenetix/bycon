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
* <http://next.progenetix.org/cgi/bycon/bin/collations.py?filters=NCIT&datasetIds=progenetix&method=counts>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    collations()
    
################################################################################

def collations():

    config = read_bycon_config( path.abspath( dir_path ) )

    byc = {
        "config": config,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "method": "default",
        "dataset_ids": ["progenetix"],
        "form_data": cgi_parse_query()
    }

    if "method" in byc["form_data"]:
        m = byc["form_data"].getvalue("method")
        if m in byc["config"]["collation_methods"].keys():
            byc["method"] = m

    method_keys = byc["config"]["collation_methods"][ byc["method"] ]

    byc.update( { "collation": "" } )
    byc.update( { "filters":  parse_filters( **byc ) } )

    if "dataset_ids" in byc["form_data"]:
        d_s = byc[ "form_data" ].getlist('datasetIds')
        d_s = ','.join(d_s)
        byc["dataset_ids"] = d_s.split(',')

    # print(byc[ "filters" ])
    # print(byc["config"]["collation_prefixes"][ "default" ])
    # exit()

    if len(byc[ "filters" ]) < 1:
        byc[ "filters" ] = byc["config"]["collation_prefixes"][ "default" ]

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
            if pre not in byc["filter_defs"]:
                continue
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
