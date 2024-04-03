import csv, datetime, re, yaml
from os import environ, path, pardir
from pymongo import MongoClient

# local
from bycon_helpers import prdbug
from config import *

################################################################################
################################################################################
################################################################################

class ChroNames:
    def __init__(self):
        self.refseq_chromosomes = {}
        self.chro_aliases = {}
        self.refseq_aliases = {}
        self.__set_genome_rsrc_path()
        self.__parse_refseq_file()
        self.__chro_id_data()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def allChros(self):
        return list(set(self.chro_aliases.values()))


    # -------------------------------------------------------------------------#

    def chroAliases(self):
        return list(self.chro_aliases.keys())


    # -------------------------------------------------------------------------#

    def allRefseqs(self):
        return list(set(self.refseq_aliases.values()))


    # -------------------------------------------------------------------------#

    def refseqAliases(self):
        return list(self.refseq_aliases.keys())


    # -------------------------------------------------------------------------#

    def chro(self, s_id="___none___"):
        return self.chro_aliases.get(s_id, "___none___")


    # -------------------------------------------------------------------------#

    def refseq(self, s_id="___none___"):
        return self.refseq_aliases.get(s_id, "___none___")


    # -------------------------------------------------------------------------#

    def genomePath(self):
        return self.genome_rsrc_path


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __set_genome_rsrc_path(self):
        # TODO: catch error for missing genome edition
        genome = BYC_PARS.get("assembly_id", "GRCh38").lower()
        g_rsrc_p = path.join( PKG_PATH, "rsrc", "genomes", genome )
        self.genome_rsrc_path = g_rsrc_p
        self.refseq_file = path.join( g_rsrc_p, "refseq_chromosomes.yaml") 


    # -------------------------------------------------------------------------#

    def __parse_refseq_file(self):
        with open(self.refseq_file) as f:
            self.refseq_chromosomes = yaml.load( f , Loader=yaml.FullLoader)


    # -------------------------------------------------------------------------#

    def __chro_id_data(self):
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
        Return:
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

        v_d_refsc = self.refseq_chromosomes
        if not v_d_refsc:
            return

        for c, c_d in v_d_refsc.items():
            refseq_stripped = re.sub("refseq:", "", c_d["refseq_id"])
            self.refseq_aliases.update({
                c: c_d["refseq_id"],
                c_d["chr"]: c_d["refseq_id"],
                c_d["refseq_id"]: c_d["refseq_id"],
                refseq_stripped: c_d["refseq_id"],
                c_d["genbank_id"]: c_d["refseq_id"]
            }),
            self.chro_aliases.update({
                c: c_d["chr"],
                c_d["chr"]: c_d["chr"],
                c_d["refseq_id"]: c_d["chr"],
                refseq_stripped: c_d["chr"],
                c_d["genbank_id"]: c_d["chr"]
            })


################################################################################

class VariantTypes:
    def __init__(self, variant_type_definitions):
        self.vtds = variant_type_definitions
        self.variant_state = None
        self.child_terms = set()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def variantState(self, variant_type="___none___"):
        self.__variant_state_from_variant_type(variant_type)
        return self.variant_state


    # -------------------------------------------------------------------------#

    def variantStateId(self, variant_type="___none___"):
        self.__variant_state_from_variant_type(variant_type)
        return self.variant_state.get("id", "___none___")


    # -------------------------------------------------------------------------#

    def variantStateChildren(self, variant_type="___none___"):
        self.child_terms = set()
        self.__variant_state_from_variant_type(variant_type)
        return list(self.child_terms)


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __variant_state_from_variant_type(self, variant_type):
        v_t_defs = self.vtds
        for k, d in v_t_defs.items():
            for p, v in d.items():
                if v is None:
                    continue
                if type(v) is list:
                    continue
                if "variant_state" in p:
                    v = v.get("id", "___none___")
                if type(v) is not str:
                    continue
                if variant_type.lower() == v.lower():
                    self.variant_state = d.get("variant_state", "___none___")
                    self.child_terms.update(d.get("child_terms", []))




################################################################################

class GeneInfo:
    def __init__(self):
        self.gene_data = []


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def returnGene(self, gene_id="___none___"):
        self.__gene_id_data(gene_id, single=True)
        return self.gene_data


    # -------------------------------------------------------------------------#

    def returnGenelist(self, gene_id="___none___"):
        self.__gene_id_data(gene_id, single=False)
        return self.gene_data


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __gene_id_data(self, gene_id, single=True):
        mongo_client = MongoClient(host=DB_MONGOHOST)
        db_names = list(mongo_client.list_database_names())
        if SERVICES_DB not in db_names:
            BYC["ERRORS"].append(f"services db `{SERVICES_DB}` does not exist")
            return

        q_f_s = ["symbol", "ensembl_gene_ids", "synonyms"]
        terminator = ""
        if single is True:
            terminator = "$"
        q_re = re.compile( r'^'+gene_id+terminator, re.IGNORECASE )
        q_list = []
        for q_f in q_f_s:
            q_list.append({q_f: q_re })
        query = { "$or": q_list }

        g_coll = mongo_client[SERVICES_DB][GENES_COLL]

        if single is True:
            gene = g_coll.find_one(query, { '_id': False } )
            if gene:
                self.gene_data = [ g_coll.find_one(query, { '_id': False } ) ]
        else:
            gene_list = list(g_coll.find(query, { '_id': False } ))
            if len(gene_list) > 0:
                self.gene_data = list(g_coll.find(query, { '_id': False } ))


