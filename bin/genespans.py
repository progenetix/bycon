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
from bycon.beacon_process_specs import *

"""podmd

* 

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    genespans()
    
################################################################################

def genespans():

    config = read_bycon_config( path.abspath( dir_path ) )
    these_prefs = read_yaml_to_object( "genespans_preference_file", **config[ "paths" ] )

    byc = {
        "config": config,
        "form_data": cgi_parse_query()
    }

    # response prototype
    r = config["response_object_schema"]
    r["data"].update({ "genes": [ ] })

    # first pre-population w/ defaults
    for d_k, d_v in these_prefs["defaults"].items():
        byc.update( { d_k: d_v } )

    # ... then modification if parameter in request
    if "assemblyId" in byc["form_data"]:
        aid = byc["form_data"].getvalue("assemblyId")
        if aid in these_prefs["assemblyId"]:
            byc["assembly_id"] = aid
        else:
            r["errors"].append("{} is not supported; fallback {} is being used!".format(aid, byc["assembly_id"]))

    r["parameters"].update( { "assemblyId": byc["assembly_id"] })

    if "geneId" in byc["form_data"]:
        byc["gene_id"] = byc["form_data"].getvalue("geneId")
    else:
        # TODO: value check & response
        r["errors"].append("No geneId value provided!")
        cgi_print_json_response( **r )

    r["parameters"].update( { "geneId": byc["gene_id"] })

    # data retrieval & response population
    mongo_client = MongoClient( )
    g_coll = mongo_client[ byc["genespans_db"] ][ byc["genespans_coll"] ]

    query = { "gene_symbol": re.compile( r'^'+byc["gene_id"] ) }

    for g in g_coll.find( query, { '_id': False } ):
        r["data"]["genes"].append( g )

    mongo_client.close( )
 
    # response
    if "callback" in byc[ "form_data" ]:
        cgi_print_json_callback(byc["form_data"].getvalue("callback"), **r )
    else:
        cgi_print_json_response(**r )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
