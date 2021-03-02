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
from bycon.lib.query_generation import create_and_or_query_for_list
from bycon.lib.query_execution import mongo_result_list
from lib.service_utils import *

################################################################################
################################################################################
################################################################################

def main():

    genespans()
    
################################################################################

def genespans():

    byc = initialize_service()
        
    r = create_empty_service_response(byc)

    assembly_id = byc["assembly_id"]
    if "assemblyId" in byc[ "form_data" ]:
        aid = byc[ "form_data" ].getvalue("assemblyId")
        if aid in byc["these_prefs"]["assembly_ids"]:
            assembly_id = aid
        else:
            r["meta"]["warnings"].append("{} is not supported; fallback {} is being used!".format(aid, assembly_id))
    if "filterPrecision" in byc[ "form_data" ]:
        byc["query_precision"] = byc["form_data"].getvalue('filterPrecision')
    
    response_add_parameter(r, "assemblyId", assembly_id)

    if "geneSymbol" in byc[ "form_data" ]:
        gene_id = byc[ "form_data" ].getvalue("geneSymbol")
        response_add_parameter(r, "geneSymbol", gene_id)
    else:
        # TODO: value check & response
        response_add_error(r, 422, "No geneSymbol value provided!" )

    cgi_break_on_errors(r, byc)

    # data retrieval & response population
    q_list = [ ]
    for q_f in byc["query_fields"]:
        if "start" in byc["query_precision"]:
            q_list.append( { q_f: re.compile( r'^'+gene_id, re.IGNORECASE ) } )
        else:
            q_list.append( { q_f: re.compile( r'^'+gene_id+'$', re.IGNORECASE ) } )
    query = create_and_or_query_for_list('$or', q_list)

    results, e = mongo_result_list( byc["db"], byc["coll"], query, { '_id': False } )
    if e:
        response_add_error(r, 422, e )

    cgi_break_on_errors(r, byc)

    populate_service_response(r, results)
    cgi_print_json_response( byc[ "form_data" ], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
