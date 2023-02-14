#!/usr/bin/env python3

import cgi, cgitb
import re, json
from os import path, pardir
import sys
from pymongo import MongoClient

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

################################################################################
################################################################################
################################################################################

def main():

    genespans()
    
################################################################################

def genespans():

    initialize_bycon_service(byc)        
    parse_variant_parameters(byc)
    generate_genomic_intervals(byc)
    create_empty_service_response(byc)

    v_rs_chros = byc["variant_definitions"]["chro_aliases"]

    assembly_id = byc["assembly_id"]
    if "assembly_id" in byc[ "form_data" ]:
        aid = byc[ "form_data" ]["assembly_id"]
        if aid in byc["service_config"]["assembly_ids"]:
            assembly_id = aid
        else:
            byc["service_response"]["meta"]["warnings"].append("{} is not supported; fallback {} is being used!".format(aid, assembly_id))
            
    if "filter_precision" in byc["form_data"]:
        byc["query_precision"] = byc["form_data"]["filter_precision"]
    else:
        byc["query_precision"] = "start"

    for mk, mv in byc["service_config"]["meta"].items():
        byc["service_response"]["meta"].update({mk: mv})

    gene_id = rest_path_value("genespans")

    if not "empty_value" in gene_id:
        response_add_received_request_summary_parameter(byc, "geneId", gene_id)
        byc.update({"query_precision": "exact"})
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
    # response_add_received_request_summary_parameter(byc, "processed_query", query)

    results, e = mongo_result_list( byc["db"], byc["coll"], query, { '_id': False } )
    response_add_error(byc, 422, e )
    cgi_break_on_errors(byc)

    for gene in results:
        _gene_add_cytobands(gene, byc)

    e_k_s = byc["service_config"]["method_keys"]["genespan"]

    if "method" in byc:
        if "genespan" in byc["method"]:
            for i, g in enumerate(results):
                g_n = {}
                for k in byc["service_config"]["method_keys"]["genespan"]:
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

def _gene_add_cytobands(gene, byc):

    v_rs_chros = byc["variant_definitions"]["chro_aliases"]
    gene.update({"cytobands": None})

    acc = gene.get("accession_version", "NA")
    if acc not in v_rs_chros:
        return gene

    start = gene.get("start", None)
    end = gene.get("end", None)
    if start is None or end is None:
        return gene

    chro = v_rs_chros.get( acc, "")
    chro_bases = "{}:{}-{}".format(chro, gene.get("start", ""), gene.get("end", ""))
    cytoBands, chro, start, end = bands_from_chrobases(chro_bases, byc)
    cb_label = cytobands_label( cytoBands )
    gene.update({"cytobands": "{}{}".format(chro, cb_label)})

    return gene

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
