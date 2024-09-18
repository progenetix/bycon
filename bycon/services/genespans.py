#!/usr/bin/env python3
import re, json, sys, traceback
from os import environ, path

from bycon import *

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from service_helpers import *
from service_response_generation import *

"""
* http://progenetix.test/services/genespans/MYC
* http://progenetix.test/services/genespans/?geneId=MYC
"""

################################################################################
################################################################################
################################################################################

def main():
    try:
        genespans()
    except Exception:
        print_text_response(traceback.format_exc(), 302)


################################################################################

def genespans():
    """
    """
    initialize_bycon_service()
    read_service_prefs("genespans", services_conf_path)

    # form id assumes start match (e.g. for autocompletes)
    r = ByconautServiceResponse()
    gene_id = rest_path_value("genespans")
    if gene_id:
        # REST path id assumes exact match
        results = GeneInfo().returnGene(gene_id)
    else:
        gene_ids = BYC_PARS.get("gene_id", [])
        gene_id = gene_ids[0] if len(gene_ids) > 0 else None
        results = GeneInfo().returnGenelist(gene_id)

    if len(BYC["ERRORS"]) > 0:
        BeaconErrorResponse().response(422)

    for gene in results:
        _gene_add_cytobands(gene)

    s_c = BYC.get("service_config", {})
    e_k_s = s_c["method_keys"]["genespan"]
    if "genespan" in str(BYC_PARS.get("method", "___none___")):
        for i, g in enumerate(results):
            g_n = {}
            for k in e_k_s:
                g_n.update({k: g.get(k, "")})
            results[i] = g_n

    if "text" in BYC_PARS.get("output", "___none___"):
        open_text_streaming()
        for g in results:
            s_comps = []
            for k in e_k_s:
                s_comps.append(str(g.get(k, "")))
            print("\t".join(s_comps))
        exit()

    print_json_response(r.populatedResponse(results))


################################################################################

def _gene_add_cytobands(gene):

    chro_names = ChroNames()
    gene.update({"cytobands": None})

    acc = gene.get("accession_version", "NA")
    if acc not in chro_names.chroAliases():
        return gene

    chro = chro_names.chro(acc)
    start = gene.get("start")
    end = gene.get("end")
    if not start or not end:
        return gene

    gene.update({"cytobands": f'{chro}{cytobands_label_from_positions(chro, start, end)}'})

    return gene

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
