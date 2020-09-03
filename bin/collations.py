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
from bycon.cgi_utils import *
from bycon.beacon_parse_filters import *
from bycon.beacon_process_specs import *

"""podmd

* <https://progenetix.org/services/collations/?filters=NCIT>
* <http://progenetix.org/cgi/bycon/bin/collations.py?filters=NCIT&datasetIds=progenetix&method=counts>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    collations("collations")
    
################################################################################

def collations(service):

    config = read_bycon_config( path.abspath( dir_path ) )
    these_prefs = read_service_prefs( service, dir_path )

    byc = {
        "config": config,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "form_data": cgi_parse_query()
    }

    # first pre-population w/ defaults
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    # ... then modification if parameter in request
    if "method" in byc["form_data"]:
        m = byc["form_data"].getvalue("method")
        if m in these_prefs["methods"].keys():
            byc["method"] = m

    # the method keys can be overriden with "deliveryKeys"
    d_k = form_return_listvalue( byc["form_data"], "deliveryKeys" )
    if len(d_k) < 1:
        d_k = these_prefs["methods"][ byc["method"] ]

    byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
    byc.update( { "filters": parse_filters( **byc ) } )

    # response prototype
    r = config["response_object_schema"]

    # TODO: move somewhere
    if len(byc[ "dataset_ids" ]) < 1:
      r["errors"].append( "No `datasetIds` parameter provided." )
    if len(byc[ "dataset_ids" ]) > 1:
      r["errors"].append( "More than 1 `datasetIds` value was provided." )
    if len(r["errors"]) > 0:
      cgi_print_json_response( byc["form_data"], r )

    ds_id = byc[ "dataset_ids" ][ 0 ]

    # saving the parameters to the response
    for p in ["dataset_ids", "method", "filters"]:
        r["parameters"].update( { p: byc[ p ] } )

    # data retrieval & response population
    mongo_client = MongoClient( )
    mongo_db = mongo_client[ ds_id ]
    r["data"].update( { "subsets": [ ] } )
    for f in byc[ "filters" ]:
        query = { "id": re.compile(r'^'+f ) }
        pre = re.split('-|:', f)[0]
        c =  byc["filter_defs"][ pre ]["collation"]
        mongo_coll = mongo_db[ c ]
        for subset in mongo_coll.find( query ):
            s = { }
            for k in d_k:
                # TODO: harmless hack
                if k in subset.keys():
                    if k == "count":
                        s[ k ] = int(subset[ k ])
                    else:
                        s[ k ] = subset[ k ]
                else:
                    s[ k ] = None
            r["data"]["subsets"].append( s )
            # r["data"]["collations"].append( s )
    mongo_client.close( )

    # TODO: testing only or general option?
    if "responseFormat" in byc["form_data"]:
        r_f = byc["form_data"].getvalue("responseFormat")
        if "simplelist" in r_f:
            r = r["data"]["subsets"]
 
    # response
    cgi_print_json_response( byc["form_data"], r )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
