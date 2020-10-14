#!/usr/local/bin/python3

import cgi, cgitb
import re, json
import sys, os
from pymongo import MongoClient

# local
dir_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.abspath(dir_path), '..'))
from bycon.cgi_utils import *
from bycon.read_specs import *

"""podmd
* <https://progenetix.org/services/genespans?geneId=CDKN2>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    genespans("genespans")
    
################################################################################

def genespans(service):

    config = read_bycon_config( os.path.abspath( dir_path ) )
    these_prefs = read_named_prefs( service, dir_path )
    form_data = cgi_parse_query()
    defs = these_prefs["defaults"]
    
    # response prototype
    r = config["response_object_schema"]
    r["response_type"] = service

    assembly_id = defs["assembly_id"]
    if "assemblyId" in form_data:
        aid = form_data.getvalue("assemblyId")
        if aid in these_prefs["assemblyId"]:
            assembly_id = aid
        else:
            assembly_id = defs["assembly_id"]
            r["warnings"].append("{} is not supported; fallback {} is being used!".format(aid, assembly_id))
    r["parameters"].update( { "assemblyId": assembly_id })

    if "geneId" in form_data:
        gene_id = form_data.getvalue("geneId")
    else:
        # TODO: value check & response
        r["errors"].append("No geneId value provided!")
        cgi_print_json_response( form_data, r, 422 )

    r["parameters"].update( { "geneId": gene_id })

    # data retrieval & response population
    # query options may be expanded - current list + sole gene_id is a bit odd
    # TODO: positional query
    q_list = [ ]
    for q_f in defs["query_fields"]:
        q_list.append( { q_f: re.compile( r'^'+gene_id, re.IGNORECASE ) } )
    if len(q_list) > 1:
        query = { '$and': q_list }
    else:
        query = q_list[0]

    mongo_client = MongoClient( )
    g_coll = mongo_client[ defs["db"] ][ defs["coll"] ]
    for g in g_coll.find( query, { '_id': False } ):
        r["data"].append( g )
    mongo_client.close( )

    r[service+"_count"] = len(r["data"])

    if r[service+"_count"] < 1:
        r["errors"].append("No matching gene...")
        cgi_print_json_response( form_data, r, 422 )
 
    cgi_print_json_response( form_data, r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
