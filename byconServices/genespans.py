from os import path
from humps import decamelize

from bycon import (
    BeaconErrorResponse,
    BYC,
    BYC_PARS,
    ChroNames,
    Cytobands,
    GeneInfo,
    prdbug,
    print_json_response
)

from byconServiceLibs import ByconServiceResponse, read_service_prefs

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )


def genespans():
    """
    The `genespans` function provides a JSON response with the coordinates of
    matching gene IDs.

    #### Examples (using the Progenetix resource as endpoint):

    * https://progenetix.test/services/genespans/MYC
    * https://progenetix.test/services/genespans/?geneId=MYC
    """

    # form id assumes start match (e.g. for autocompletes)
    if len(gene_ids := BYC.get("path_ids", [])) == 1:
        # REST path id assumes exact match
        results = GeneInfo().returnGene(gene_ids[0])
    else:
        gene_ids = BYC_PARS.get("gene_id", [])
        # print(type(BYC_PARS.get("gene_id", [])))
        gene_id = gene_ids[0] if len(gene_ids) > 0 else None
        # print(gene_id)
        # exit()
        results = GeneInfo().returnGenelist(gene_id)

    BeaconErrorResponse().respond_if_errors()

    for gene in results:
        _gene_add_cytobands(gene)

    # TODO: In some general method
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

    # prdbug(f'????')

    ByconServiceResponse().print_populated_response(results)


################################################################################

def _gene_add_cytobands(gene):
    # TODO: this should be a method in the GeneInfo class

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

    gene.update({
        "cytobands": f'{Cytobands().cytobands_label_from_positions(chro, start, end)}',
        "chromosome": chro,
        "reference_name": chro_names.refseq(acc)
    })

    return gene

