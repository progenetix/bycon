#!/usr/local/bin/python3

import cgi, cgitb
import re, json
from os import path, pardir
import sys
from pymongo import MongoClient

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import *
from bycon.lib.read_specs import *
from bycon.lib.query_execution import mongo_result_list
from lib.service_utils import *

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

    byc = {
        "pkg_path": pkg_path,
        "config": read_bycon_configs_by_name( "defaults" ),
        "form_data": cgi_parse_query()
    }
    
    these_prefs = read_local_prefs( service, dir_path )
    
    r = create_empty_service_response(**these_prefs)

    assembly_id = these_prefs["defaults"]["assembly_id"]
    if "assemblyId" in byc[ "form_data" ]:
        aid = byc[ "form_data" ].getvalue("assemblyId")
        if aid in these_prefs["assembly_ids"]:
            assembly_id = aid
        else:
            r["meta"]["warnings"].append("{} is not supported; fallback {} is being used!".format(aid, assembly_id))
    r["meta"]["parameters"].append( { "assemblyId": assembly_id })

    if "geneId" in byc[ "form_data" ]:
        gene_id = byc[ "form_data" ].getvalue("geneId")
    else:
        # TODO: value check & response
        r["meta"]["errors"].append("No geneId value provided!")
        cgi_print_json_response( byc[ "form_data" ], r, 422 )

    r["meta"]["parameters"].append( { "geneId": gene_id })

    # data retrieval & response population
    # query options may be expanded - current list + sole gene_id is a bit odd
    # TODO: positional query
    q_list = [ ]
    for q_f in these_prefs["defaults"]["query_fields"]:
        q_list.append( { q_f: re.compile( r'^'+gene_id, re.IGNORECASE ) } )
    if len(q_list) > 1:
        query = { '$and': q_list }
    else:
        query = q_list[0]

    results, error = mongo_result_list( these_prefs["defaults"]["db"], these_prefs["defaults"]["coll"], query, { '_id': False } )
    if error:
        r["meta"]["errors"].append( error )
        cgi_print_json_response( byc[ "form_data" ], r, 422 )

    populate_service_response(r, results)
    cgi_print_json_response( byc[ "form_data" ], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
