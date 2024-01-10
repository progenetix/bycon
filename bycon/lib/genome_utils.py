import csv, datetime, re, yaml
from os import environ, path, pardir
from pymongo import MongoClient

# local
from bycon_helpers import generate_id, mongo_result_list
from variant_mapping import ByconVariant

bycon_lib_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( bycon_lib_path, pardir )

################################################################################
################################################################################
################################################################################

def generate_genomic_mappings(byc):
    set_genome_rsrc_path(byc)
    parse_refseq_file(byc)
    translate_reference_ids(byc)


################################################################################

def set_genome_rsrc_path(byc):

    # TODO: catch error for missing genome edition
    # TODO: adjust resource file use for local configuration
    g_map = byc["interval_definitions"]["genome_path_ids"].get("values", {})
    genome = byc["interval_definitions"]["genome_default"]
    if "varguments" in byc:
        p_g = byc["varguments"].get("assembly_id")
        if p_g is not None:
            genome = p_g

    genome = genome.lower()

    # TODO / BUG: next breaks e.g. "mSarHar1.11" -> therefore mapping...
    genome = re.sub( r"(\w+?)([^\w]\w+?)", r"\1", genome)
    if genome in g_map.keys():
        genome = g_map[ genome ]

    byc.update({"genome_rsrc_path": path.join( pkg_path, *byc["genomes_path"], genome ) })


################################################################################

def parse_refseq_file(byc):
    refseq_file = path.join( byc["genome_rsrc_path"], "refseq_chromosomes.yaml") 
    with open( refseq_file ) as f:
        r_c = yaml.load( f , Loader=yaml.FullLoader)

    byc.update({ "refseq_chromosomes": r_c })


################################################################################

def translate_reference_ids(byc):

    """
    Input: "refseq_chromosomes" object:
    Example:
    ```
      chr3:
        chr: "3"
        genbank_id: "CM000665.2"
        refseq_id: "refseq:NC_000003.12"
        length: 198295559
    ```
    Return: added objects in byc["variant_request_definitions"]
      - "chro_refseq_ids" - refseq id for each chromosome
          - "15": "refseq:NC_000015.10"
      - "refseq_chronames": chromosome for each refseq id
          - "refseq:NC_000015.10": "15"
      - "refseq_aliases": all alternative names for a refseq id are keys
          - "15": "refseq:NC_000015.10"
          - "chr15": "refseq:NC_000015.10"
          - "refseq:NC_000015.10": "refseq:NC_000015.10"
          - "NC_000015.10": "refseq:NC_000015.10"
          - "CM000677.2": "refseq:NC_000015.10"
        "chro_aliases": all aliases for a stripped chromosome name
          - "15": "15"
          - "chr15": "15"
          - "refseq:NC_000015.10": "15"
          - "NC_000015.10": "15"
          - "CM000677.2": "15"
    """

    v_d_refsc = byc.get("refseq_chromosomes")
    if v_d_refsc is None:
        return

    c_r = {}    # keys are the bare chromosome names e.g. "15"
    r_c = {}    # keys are the refseq_id
    r_a = {}    # keys are all options, values the refseq_id
    c_a = {}    # keys are all options, values the chromosome

    for c, c_d in v_d_refsc.items():
        refseq_stripped = re.sub("refseq:", "", c_d["refseq_id"])
        c_r.update({ c_d["chr"]: c_d["refseq_id"] })
        r_c.update({ c_d["refseq_id"]: c_d["chr"] })
        r_a.update({
            c: c_d["refseq_id"],
            c_d["chr"]: c_d["refseq_id"],
            c_d["refseq_id"]: c_d["refseq_id"],
            refseq_stripped: c_d["refseq_id"],
            c_d["genbank_id"]: c_d["refseq_id"]
        }),
        c_a.update({
            c: c_d["chr"],
            c_d["chr"]: c_d["chr"],
            c_d["refseq_id"]: c_d["chr"],
            refseq_stripped: c_d["chr"],
            c_d["genbank_id"]: c_d["chr"]
        })

    byc.update({
        "genome_aliases": {
            "chro_refseq_ids": c_r,
            "refseq_chronames": r_c,
            "refseq_aliases": r_a,
            "chro_aliases": c_a
        }
    })


################################################################################

def retrieve_gene_id_coordinates(gene_id, precision, byc):

    mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    db_names = list(mongo_client.list_database_names())

    services_db = byc.get("services_db", "___none___")
    if services_db not in db_names:
        return [], f"services db `{services_db}` does not exist"

    genes_coll = byc.get("genes_coll")
    if not genes_coll:
        return [], "no `genes_coll` parameter in `config.yaml`"

    q_f_s = byc.get("query_fields", ["symbol", "ensembl_gene_ids", "synonyms"])

    greed = "$"
    if precision == "start":
        greed = ""

    q_re = re.compile( r'^'+gene_id+greed, re.IGNORECASE )
    q_list = []

    for q_f in q_f_s:
        q_list.append({q_f: q_re })

    query = { "$or": q_list }
    results, e = mongo_result_list( services_db, genes_coll, query, { '_id': False } )

    return results, e
