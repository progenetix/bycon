import csv, datetime, re, yaml
from os import environ, path, pardir
from pymongo import MongoClient

# local
from bycon_helpers import generate_id, mongo_result_list, prdbug

bycon_lib_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( bycon_lib_path, pardir )

################################################################################
################################################################################
################################################################################

def set_genome_rsrc_path(byc):

    # TODO: catch error for missing genome edition
    # TODO: adjust resource file use for local configuration
    g_map = byc["interval_definitions"]["genome_path_ids"].get("values", {})
    genome = byc["interval_definitions"]["genome_default"]
    if "varguments" in byc:
        genome = byc["varguments"].get("assembly_id", genome)
    genome = genome.lower()

    # TODO / BUG: next breaks e.g. "mSarHar1.11" -> therefore mapping...
    genome = re.sub( r"(\w+?)([^\w]\w+?)", r"\1", genome)
    if genome in g_map.keys():
        genome = g_map[ genome ]

    byc.update({"genome_rsrc_path": path.join( pkg_path, *byc["genomes_path"], genome ) })


################################################################################

class ChroNames:
    def __init__(self, byc):
        self.refseq_file = path.join( byc["genome_rsrc_path"], "refseq_chromosomes.yaml") 
        self.refseq_chromosomes = {}
        self.chro_aliases = {}
        self.refseq_aliases = {}
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
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __parse_refseq_file(self):
        with open( self.refseq_file ) as f:
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

class GeneInfo:
    def __init__(self, db_config):
        self.db_config = db_config
        self.error = None
        self.gene_data = []

    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def returnGene(self, gene_id="___none___"):
        self.__gene_id_data(gene_id, single=True)
        return self.gene_data, self.error

    # -------------------------------------------------------------------------#

    def returnGenelist(self, gene_id="___none___"):
        self.__gene_id_data(gene_id, single=False)
        return self.gene_data, self.error

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __gene_id_data(self, gene_id, single=True):
        mdb_c = self.db_config
        db_host = mdb_c.get("host", "localhost")
        s_db = mdb_c.get("services_db", "___none___")
        g_coll = mdb_c.get("genes_coll", "___none___")

        mongo_client = MongoClient(host=db_host)
        db_names = list(mongo_client.list_database_names())
        if s_db not in db_names:
            self.error = f"services db `{s_db}` does not exist"
            return
        if "___none___" in g_coll:
            self.error = "no `genes_coll` parameter in `config.yaml`"
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

        if single is True:
            gene = mongo_client[s_db][g_coll].find_one(query, { '_id': False } )
            if gene:
                self.gene_data = [ mongo_client[s_db][g_coll].find_one(query, { '_id': False } ) ]
        else:
            gene_list = list(mongo_client[s_db][g_coll].find(query, { '_id': False } ))
            if len(gene_list) > 0:
                self.gene_data = list(mongo_client[s_db][g_coll].find(query, { '_id': False } ))


