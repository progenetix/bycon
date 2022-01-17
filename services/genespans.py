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

from beaconServer import *

################################################################################
################################################################################
################################################################################

def main():

    genespans()
    
################################################################################

def genespans():

    initialize_service(byc)        
    create_empty_service_response(byc)

    assembly_id = byc["assembly_id"]
    if "assemblyId" in byc[ "form_data" ]:
        aid = byc[ "form_data" ]["assemblyId"]
        if aid in byc["this_config"]["assembly_ids"]:
            assembly_id = aid
        else:
            byc["service_response"]["meta"]["warnings"].append("{} is not supported; fallback {} is being used!".format(aid, assembly_id))
            
    if "filterPrecision" in byc["form_data"]:
        byc["query_precision"] = byc["form_data"]["filterPrecision"]
    else:
        byc["query_precision"] = "start"

    for mk, mv in byc["this_config"]["meta"].items():
        byc["service_response"]["meta"].update({mk: mv})

    gene_id = rest_path_value("genespans")

    if not "empty_value" in gene_id:
        response_add_received_request_summary_parameter(byc, "geneSymbol", gene_id)
    elif "geneSymbol" in byc[ "form_data" ]:
        gene_id = byc[ "form_data" ]["geneSymbol"]
        response_add_received_request_summary_parameter(byc, "gene_symbol", gene_id)
    else:
        # TODO: value check & response
        response_add_error(byc, 422, "No geneSymbol value provided!" )

    cgi_break_on_errors(byc)

    # data retrieval & response population
    q_list = [ ]
    for q_f in byc["query_fields"]:
        if "start" in byc["query_precision"]:
            q_list.append( { q_f: re.compile( r'^'+gene_id, re.IGNORECASE ) } )
        else:
            q_list.append( { q_f: re.compile( r'^'+gene_id+'$', re.IGNORECASE ) } )
    query = create_and_or_query_for_list('$or', q_list)
    response_add_received_request_summary_parameter(byc, "processed_query", query)

    results, e = mongo_result_list( byc["db"], byc["coll"], query, { '_id': False } )
    if e:
        response_add_error(byc, 422, e )

    cgi_break_on_errors(byc)

    if "method" in byc:
        if "genespan" in byc["method"]:
            for i, g in enumerate(results):
                g_n = {}
                for k in byc["this_config"]["methods"]["genespan"]:
                    if not k in g:
                        continue
                    g_n.update({k:g[k]})
                results[i] = g_n


    populate_service_response( byc, results)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
