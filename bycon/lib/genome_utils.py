import csv, re, yaml
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
        self.ga4ghSQ_aliases = {}
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

    def ga4ghSQs(self):
        return list(set(self.ga4ghSQ_aliases.values()))


    # -------------------------------------------------------------------------#

    def refseqAliases(self):
        return list(self.refseq_aliases.keys())


    # -------------------------------------------------------------------------#

    def chro(self, s_id="___none___"):
        return self.chro_aliases.get(s_id)


    # -------------------------------------------------------------------------#

    def refseq(self, s_id="___none___"):
        return self.refseq_aliases.get(s_id, "___none___")


    # -------------------------------------------------------------------------#

    def ga4ghSQ(self, s_id="___none___"):
        return self.ga4ghSQ_aliases.get(s_id, "___none___")


    # -------------------------------------------------------------------------#

    def refseqLabeled(self, s_id="___none___"):
        chrLabs = []
        for chrId, chr_def in self.refseq_chromosomes.items():
            chrLabs.append({chr_def["refseq_id"]: chrId})
        return chrLabs


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
          - "ga4ghSQ_aliases": all alternative names for a ga4gh SQ id are keys
              - "15": "refseq:NC_000015.10"
              - "chr15": "refseq:NC_000015.10"
              - "refseq:NC_000015.10": "refseq:NC_000015.10"
              - "NC_000015.10": "refseq:NC_000015.10"
              - "CM000677.2": "refseq:NC_000015.10"
          - "chro_aliases": all aliases for a stripped chromosome name
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
            rid = c_d.get("refseq_id", "___none___")
            rid_stripped = re.sub("refseq:", "", rid)
            sqid = c_d.get("sequence_id", "___none___")
            sqid_stripped = re.sub("ga4gh:", "", sqid)
            chro = c_d.get("chr", "___none___")
            gbid = c_d.get("genbank_id", "___none___")
            for alias in [c, chro, rid, rid_stripped, sqid, sqid_stripped, gbid]:
                if alias == "___none___":
                    continue
                self.ga4ghSQ_aliases.update({alias: sqid})
                self.refseq_aliases.update({alias: rid})
                self.chro_aliases.update({alias: chro})


################################################################################

class VariantTypes:
    def __init__(self):
        self.vtds = BYC.get("variant_type_definitions", {})
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
        for k, d in self.vtds.items():
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
################################################################################
################################################################################

class Cytobands():
    """
    The `Cytobands()` class provides methods to access cytoband information from
    a standard UCSC-style cytoband file (cytoBandIdeo.txt), to filter those for
    cytoband or genomic ranges and to convert between cytoband and genomic coordinates.
    """

    def __init__(self):
        self.cytobands = [ ]
        self.cytolimits = { }
        self.genome_size = 0
        self.filtered_bands = []
        self.chro = None
        self.start = None
        self.end = None
        self.ChroNames = ChroNames()
        self.cytoband_response = {}
        self.cytobands_label = ""
        self.sorted_chros = BYC["interval_definitions"]["chromosomes"]
        arg_defs = BYC["argument_definitions"].get("$defs", {"cyto_bands":{}, "chro_bases":{}})
        self.cytob_pat = re.compile(arg_defs["cyto_bands"].get("pattern", "___error___"))
        self.chrob_pat = re.compile(arg_defs["chro_bases"].get("pattern", "___error___"))

        self.__parse_cytoband_file()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def get_all_cytobands(self):
        return self.cytobands


    # -------------------------------------------------------------------------#

    def get_all_cytolimits(self):
        return self.cytolimits


    # -------------------------------------------------------------------------#

    def get_genome_size(self):
        return self.genome_size


    # -------------------------------------------------------------------------#

    def cytobands_response(self):
        self.__cytobands_from_request_pars()
        self.__cytobands_response_object()
        return self.cytoband_response


    # -------------------------------------------------------------------------#

    def bands_from_cytostring(self, cytoband=""):
        self.cytostring = cytoband
        self.__bands_from_cytobands()
        return self.filtered_bands, self.chro, self.start, self.end


    # -------------------------------------------------------------------------#

    def cytobands_label_from_positions(self, chro, start, end):
        self.__cytobands_list_from_positions(chro, start, end)
        self.__cytobands_label()
        return self.cytobands_label

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __cytobands_from_request_pars(self):
        if (c_b := BYC_PARS.get("cyto_bands")):
            self.cytostring = c_b
            self.__bands_from_cytobands()
        if (c_b := BYC_PARS.get("chro_bases", [])):
            self.filtered_bands, self.chro, self.start, self.end = self.__bands_from_chrobases(c_b)


    # -------------------------------------------------------------------------#

    def __bands_from_chrobases(self, chro_bases):
        if not self.chrob_pat.match(chro_bases):
            self.filtered_bands = []
            self.chro = "NA"
            self.start = 0
            self.end = 0
            return
        chro, cb_start, cb_end = self.chrob_pat.match(chro_bases).group(2,3,5)
        self.__cytobands_list_from_positions(chro, cb_start, cb_end)


    # -------------------------------------------------------------------------#

    def __cytobands_response_object(self):
        if len(self.filtered_bands) < 1:
            BYC["ERRORS"].append("No matching cytobands!")
            return

        self.__cytobands_label()
        size = int(self.end - self.start)
        chro_bases = f'{self.chro}:{self.start}-{self.end}'
        sequence_id = self.ChroNames.refseq(self.chro)

        self.cytoband_response = {
            "info": {
                "cytoBands": self.cytobands_label,
                "bandList": [x['chroband'] for x in self.filtered_bands ],
                "chroBases": chro_bases,
                "referenceName": self.chro,
                "size": size,
            },        
            "chromosome_location": {
                "type": "ChromosomeLocation",
                "species_id": "taxonomy:9606",
                "chr": self.chro,
                "interval": {
                    "start": self.filtered_bands[0]["cytoband"],
                    "end": self.filtered_bands[-1]["cytoband"],
                    "type": "CytobandInterval"
                }
            },
            "genomic_location": {
                "type": "SequenceLocation",
                "sequence_id": sequence_id,
                "interval": {
                    "start": {
                        "type": "Number",
                        "value": self.start
                    },
                    "end": {
                        "type": "Number",
                        "value": self.end
                    },
                    "type": "SequenceInterval"
                }
            }
        }


    # -------------------------------------------------------------------------#
    # -------------------------------------------------------------------------#

    def __parse_cytoband_file(self):
        g_rsrc_p = self.ChroNames.genomePath()
        cb_file = path.join(g_rsrc_p, "cytoBandIdeo.txt")
        cb_keys = [ "chro", "start", "end", "cytoband", "staining" ]
        i = 0
        c_bands = [ ]
        with open(cb_file) as cb_f:                                                                                          
            for c_band in csv.DictReader(filter(lambda row: row.startswith('#') is False, cb_f), fieldnames=cb_keys, delimiter='\t'):
                c_bands.append(c_band)

        #--------------------------------------------------------------------------#

        # !!! making sure the chromosomes are sorted !!!
        # TODO: should be in ChroNames?
        for chro in self.sorted_chros:
            chro = str(chro)
            c_m = f'chr{chro}'
            chrobands = [ ]
            for cb in c_bands:
                if cb["chro"] == c_m:
                    cb["i"] = i
                    cb["chro"] = cb["chro"].replace("chr", "")
                    cb["chroband"] = f'{cb["chro"]}{cb["cytoband"]}'
                    self.cytobands.append(dict(cb))
                    chrobands.append(dict(cb))
                    i += 1
            self.cytolimits.update({
                chro: {
                    "chro": [ int(chrobands[0]["start"]), int(chrobands[-1]["end"]) ],
                    "size": int(chrobands[-1]["end"]) - int(chrobands[0]["start"]),
                    "p": self.__arm_base_range("p", chrobands),
                    "q": self.__arm_base_range("q", chrobands)
                }
            })
            self.genome_size += int(chrobands[-1]["end"])

    #--------------------------------------------------------------------------#

    def __bands_from_cytobands(self):
        end_re = re.compile(r"^([pq]\d.*?)\.?\d$")
        arm_re = re.compile(r"^([pq]).*?$")
        p_re = re.compile(r"^p.*?$")
        q_re = re.compile(r"^q.*?$")

        chr_bands = self.cytostring

        if "p10" in chr_bands:
            chr_bands = re.sub("p10", "pcen", chr_bands)
        if "q10" in chr_bands:
            chr_bands = re.sub("q10", "qcen", chr_bands)

        if not self.cytob_pat.match(chr_bands):
            return([], "", "", "")

        chro, cb_start, cb_end = self.cytob_pat.match(chr_bands).group(1,2,3)
        cytobands = list(filter(lambda d: d["chro"] == chro, self.cytobands.copy()))

        if len(cytobands) < 10:
            BYC["ERRORS"].append(f"No matching cytobands for chromosome {chro}!")
            return

        if cb_start is None and cb_end is None:
            self.filtered_bands = cytobands
            self.chro = chro
            self.start = int(cytobands[0]["start"])
            self.end = int(cytobands[-1]["end"])
            return

        p_bands = list(filter(lambda d: p_re.match(d["cytoband"]), cytobands))
        q_bands = list(filter(lambda d: q_re.match(d["cytoband"]), cytobands))

        # if there was no end, the start band is queried again until its last match
        if cb_end is None:
            cb_end = cb_start

        if "qter" in cb_start:
            cb_start = cytobands[-1]["cytoband"]
        if "qter" in cb_end:
            cb_end = cytobands[-1]["cytoband"]
        if "pter" in cb_start:
            cb_start = cytobands[0]["cytoband"]
        if "pter" in cb_end:
            cb_end = cytobands[0]["cytoband"]
        if "pcen" in cb_start:
            cb_start = p_bands[-1]["cytoband"]
        if "pcen" in cb_end:
            cb_end = p_bands[-1]["cytoband"]
        if "qcen" in cb_start:
            cb_start = q_bands[0]["cytoband"]
        if "qcen" in cb_end:
            cb_end = q_bands[0]["cytoband"]

        if "p" in cb_end:
            if "q" in cb_start:
                cb_start, cb_end = cb_end, cb_start

        # using a numeric comparison to sort bands for p higher to lower
        cb_re = re.compile(r'^([pq])((\d)(?:\d(?:\.\d\d?\d?)?)?)$', re.IGNORECASE)
        if cb_re.match(cb_start) and cb_re.match(cb_end):
            fb1 = float( cb_re.match(cb_start).group(2) )
            fb2 = float( cb_re.match(cb_end).group(2) )
            arm1 = cb_re.match(cb_start).group(1)
            arm2 = cb_re.match(cb_end).group(1)
            mb1 = int( cb_re.match(cb_start).group(3) )
            mb2 = int( cb_re.match(cb_end).group(3) )
            if arm1 == arm2:
                if "p" in arm1:
                    if not mb1 > mb2:
                        if fb2 > fb1:
                            cb_start, cb_end = cb_end, cb_start
                elif "q" in arm1:
                    if not mb2 > mb1:
                        if fb2 < fb1:
                            cb_start, cb_end = cb_end, cb_start

        # print("\n", chro, cb_start, cb_end, chr_bands)

        # TODO: this is ugly - somehow had problems w/ recursion version :-/
        start_bands = self.__match_bands(cb_start, cytobands)
        if len(start_bands) < 1:
            if end_re.match(cb_start):
                band = end_re.match(cb_start).group(1)
                start_bands = self.__match_bands(band, cytobands)
                if len(start_bands) < 1:
                    if arm_re.match(cb_start):
                        band = arm_re.match(cb_start).group(1)
                        start_bands = self.__match_bands(band, cytobands)

        end_bands = self.__match_bands(cb_end, cytobands)
        if len(end_bands) < 1:
            if end_re.match(cb_end):
                band = end_re.match(cb_end).group(1)
                end_bands = self.__match_bands(band, cytobands)
                if len(end_bself.ands) < 1:
                    if arm_re.match(cb_end):
                        band = arm_re.match(cb_end).group(1)
                        end_bands = self.__match_bands(band, cytobands)

        cb_from = start_bands[0]["i"]
        cb_to = end_bands[-1]["i"] + 1

        matched = self.cytobands[cb_from:cb_to]

        self.filtered_bands = matched
        self.chro = chro
        self.start = int( matched[0]["start"] )
        self.end = int( matched[-1]["end"])

    #--------------------------------------------------------------------------#

    def __match_bands(self, band, cytobands):
        cb_re = re.compile(rf"^{band}", re.IGNORECASE)
        m_b_s = list( filter(lambda d:cb_re.match(d["cytoband"]), cytobands) )
        return m_b_s


    #--------------------------------------------------------------------------#

    def __arm_base_range(self, arm, chrobands):
        if arm not in ["p","q", "P", "Q"]:
            return 0, 1
        arm_re = re.compile(rf"^{arm}", re.IGNORECASE)
        bands = list(filter(lambda d: arm_re.match(d[ "cytoband" ]), chrobands))
        return [ int(bands[0]["start"]), int(bands[-1]["end"]) ]


    #--------------------------------------------------------------------------#

    def __cytobands_list_from_positions(self, chro, start=None, end=None):
        if start:
            start = int(start)
            if not end:
                end = start + 1
            end = int(end)

        cytobands = list(filter(lambda d: d[ "chro" ] == chro, self.cytobands.copy()))
        if start == None:
            start = 0
        if end == None:
            end = int( cytoBands[-1]["end"] )

        if isinstance(start, int):
            cytobands = list(filter(lambda d: int(d[ "end" ]) > start, cytobands))
        if isinstance(end, int):
            cytobands = list(filter(lambda d: int(d[ "start" ]) < end, cytobands))

        self.filtered_bands = cytobands
        self.chro = chro
        self.start = int( cytobands[0]["start"] )
        self.end = int( cytobands[-1]["end"])


    #--------------------------------------------------------------------------#

    def __cytobands_label(self):
        if len(self.filtered_bands) < 1:
            return
            
        self.cytobands_label = f'{self.chro}{self.filtered_bands[0].get("cytoband", "")}'
        if len(self.filtered_bands) > 1:
            self.cytobands_label += self.filtered_bands[-1].get("cytoband", "")


################################################################################
################################################################################
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


