from os import path
from humps import decamelize

from bycon import (
    BeaconErrorResponse,
    BYC,
    BYC_PARS,
    ChroNames,
    cytobands_label_from_positions,
    GeneInfo,
    print_json_response,
    rest_path_value
)
from byconServiceLibs import ByconServiceResponse, read_service_prefs

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )

"""
* http://progenetix.test/services/genespans/MYC
* http://progenetix.test/services/genespans/?geneId=MYC
"""

def genespans():
    read_service_prefs("genespans", services_conf_path)

    # form id assumes start match (e.g. for autocompletes)
    gene_id = rest_path_value("genespans")
    if gene_id:
        # REST path id assumes exact match
        results = GeneInfo().returnGene(gene_id)
    else:
        gene_ids = BYC_PARS.get("gene_id", [])
        gene_id = gene_ids[0] if len(gene_ids) > 0 else None
        results = GeneInfo().returnGenelist(gene_id)

    BeaconErrorResponse().respond_if_errors()

    for gene in results:
        _gene_add_cytobands(gene)

    if len(d_k := BYC_PARS.get("delivery_keys", [])) > 0:
        for i, g in enumerate(results):
            g_n = {}
            for k in d_k:
                q_k = decamelize(k)
                g_n.update({k: g.get(q_k, "")})
            results[i] = g_n
    else:
        d_k = results[0].keys()

    if "text" in BYC_PARS.get("output", "___none___"):
        open_text_streaming()
        for g in results:
            s_comps = []
            for k in g.keys():
                s_comps.append(str(g.get(k, "")))
            print("\t".join(s_comps))
        exit()

    ByconServiceResponse().print_populated_response(results)


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

