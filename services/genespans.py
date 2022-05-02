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
    if "assembly_id" in byc[ "form_data" ]:
        aid = byc[ "form_data" ]["assembly_id"]
        if aid in byc["this_config"]["assembly_ids"]:
            assembly_id = aid
        else:
            byc["service_response"]["meta"]["warnings"].append("{} is not supported; fallback {} is being used!".format(aid, assembly_id))
            
    if "filter_precision" in byc["form_data"]:
        byc["query_precision"] = byc["form_data"]["filter_precision"]
    else:
        byc["query_precision"] = "start"

    for mk, mv in byc["this_config"]["meta"].items():
        byc["service_response"]["meta"].update({mk: mv})

    gene_id = rest_path_value("genespans")

    if not "empty_value" in gene_id:
        response_add_received_request_summary_parameter(byc, "geneId", gene_id)
    elif "gene_id" in byc[ "form_data" ]:
        gene_id = byc[ "form_data" ]["gene_id"]
        response_add_received_request_summary_parameter(byc, "geneId", gene_id)
    else:
        # TODO: value check & response
        response_add_error(byc, 422, "No geneId value provided!" )

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
    response_add_error(byc, 422, e )
    cgi_break_on_errors(byc)

    e_k_s = byc["this_config"]["method_keys"]["genespan"]

    if "method" in byc:
        if "genespan" in byc["method"]:
            for i, g in enumerate(results):
                g_n = {}
                for k in byc["this_config"]["method_keys"]["genespan"]:
                    g_n.update({k:g.get(k, "")})
                results[i] = g_n

    if "text" in byc["output"]:
        open_text_streaming(byc["env"])
        for g in results:
            s_comps = []
            for k in e_k_s:
                s_comps.append(str(g.get(k, "")))
            print("\t".join(s_comps))
        exit()

    populate_service_response( byc, results)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
