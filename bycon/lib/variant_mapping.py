import re
from copy import deepcopy
from deepmerge import always_merger
from humps import decamelize

from ga4gh.vrs.dataproxy import create_dataproxy, SequenceProxy

from vrs_translator import AdjacencyTranslator, AlleleTranslator, CnvTranslator

from parameter_parsing import prdbug, RefactoredValues
from config import *
from bycon_helpers import clean_empty_fields, get_nested_value
from schema_parsing import ByconSchemas
from genome_utils import ChroNames

################################################################################
################################################################################
################################################################################

class ByconVariant:
    def __init__(self):
        """
        # Class `ByconVariant`

        The class provides methods for the conversion of genomic variant objects
        with slight variations in their input parameters to a "canonical" intermediary
        `byc_variant` type, and from there then map per function to other formats
        (such as the Progenetix database format, VCF or VRS).

        The class is geared towards the data we currently process through the
        Progenetix platform and does not cover some use cases outside of Progenetix
        and Beacon "common use" scenarios (as of Beacon v2 / 2023).
        """
        self.vcf_variant = {}
        self.pgxseg_variant = {}

        self.ChroNames = ChroNames()
        self.variant_types = BYC.get("variant_type_definitions", {})
        self.variant_types_map = {}
        for v_t, v_d in self.variant_types.items():
            if (variant_type := v_d.get("variant_type")) and (variant_type_id := v_d.get("variant_type_id")):
                self.variant_types_map.update({variant_type: variant_type_id})

        # datatable mappings contain the "name to place in object" definitions
        # these are in essence identical to the `db_key` mappings in
        # `argument_definitions` but logically different (query vs. defiition; `default`...)
        self.datatable_mappings = BYC.get("datatable_mappings", {"$defs": {}})
        self.header_cols = self.datatable_mappings.get("ordered_pgxseg_columns", [])
        self.variant_mappings = self.datatable_mappings["$defs"].get("genomicVariant", {}).get("parameters", {})

        seqrepo_rest_service_url = 'seqrepo+file:///Users/Shared/seqrepo/2024-12-20'
        self.seqrepo_dataproxy = create_dataproxy(uri=seqrepo_rest_service_url)
        self.vrs_allele_translator = AlleleTranslator(data_proxy=self.seqrepo_dataproxy)
        self.vrs_cnv_translator = CnvTranslator(data_proxy=self.seqrepo_dataproxy, identify=False)
        self.vrs_adjacency_translator = AdjacencyTranslator(data_proxy=self.seqrepo_dataproxy, identify=False)


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def byconVariant(self, variant={}):
        self.byc_variant = variant
        self.__create_canonical_variant()
        return self.byc_variant


    # -------------------------------------------------------------------------#

    def referenceBases(self, refseq, pos_range):
        refseq = re.sub("refseq:", "", refseq)
        seq_proxy = SequenceProxy(self.seqrepo_dataproxy, refseq)
        if type(pos_range) is int:
            return seq_proxy[pos_range]
        return seq_proxy[pos_range[0]:pos_range[1]]


    # -------------------------------------------------------------------------#

    def vcfVariant(self, variant={}):
        """
        Mapping of the relevant variant parameters into an object with

        * standard VCF column headers such as as `#CHROM` as keys
        * an `INFO` key + string for CNVs
        TODO: change to vrs-python?
        """
        self.byc_variant = variant
        self.__create_canonical_variant()

        vt_defs = self.variant_types
        v = self.byc_variant

        # TODO: VCF schema in some config file...
        v_v = {
            "#CHROM": v["location"].get("chromosome", "."),
            "POS": int(v["location"].get("start", 0)) + 1,
            "ID": ".",
            "REF": v.get("reference_sequence", "."),
            "ALT": v.get("state", {}).get("sequence", "."),
            "QUAL": ".",
            "FILTER": "PASS",
            "FORMAT": "GT",
            "INFO": ""
        }

        if not v_v["ALT"]:
            v_v.update({"ALT": ""})

        if (v_s_id := v["variant_state"].get("id", "___none___")) in vt_defs.keys():
            s_a = vt_defs[v_s_id].get("VCF_symbolic_allele")
            if s_a and len(v_v["ALT"]) < 1:
                v_v.update({"ALT": s_a})

        v_l = v["info"].get("var_length", "___none___")
        if type(v_l) is int:
            if v_l >= 50:
                v_v.update({"INFO": f'IMPRECISE;SVCLAIM=D;END={v.get("end")};SVLEN={v_l}'})

        self.vcf_variant.update(v_v) 
        return self.vcf_variant


    # -------------------------------------------------------------------------#

    def vrsVariant(self, variant):
        """
        Mapping of the relevant variant parameters into a VRS object
        ... TODO ...
        """
        
        self.byc_variant = variant
        self.__create_canonical_variant()

        vt_defs = self.variant_types
        state_id = self.byc_variant.get("variant_state", {}).get("id", "___none___")
        state_defs = vt_defs.get(state_id, {})
        vrs_type = state_defs.get("VRS_type", self.byc_variant.get("type", "___none___"))

        if "Allele" in str(vrs_type):
            self.__vrs_allele()
        elif "Adjacency" in str(vrs_type):
            self.__vrs_adjacency()
        else:
            self.__vrs_cnv()

        # TODO: since the vrs_variant has been created as a new object we now
        #       add the annotation fields back (should empties be omitted?)
        for v_s in ("individual_id", "biosample_id", "analysis_id"): # "id", "variant_internal_id"
            if (v_v := self.byc_variant.get(v_s)):
                self.vrs_variant.update({v_s: v_v})
        if (r_s := self.byc_variant.get("state", {}).get("reference_sequence")):
            self.vrs_variant["state"].update({
                "reference_sequence": r_s
            })
        if len(v_a := self.byc_variant.get("variant_alternative_ids", [])) > 0:
            self.vrs_variant.update({"variant_alternative_ids": v_a})
        for v_o in ("identifiers", "molecular_attributes", "variant_level_data"): # "info",
            if (v_v := self.byc_variant.get(v_o)):
                self.vrs_variant.update({v_o: v_v})

        return self.vrs_variant


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __vrs_allele(self):
        """
        A variant with a specified sequence as a subtype of VRS `MolecularVariation`.
        This remapping just covers the formats supported in the `bycon` environment
        but does not try to accommodate all use cases.
        """
        v = self.byc_variant
        l = v.get("location", {})
        v_s = v.get("variant_state", {})
        s_id = l.get("sequence_id")
        chro = l.get("chromosome")
        # pgxseg_l = self.__pgxseg_line().replace("\t", "::")
        
        gnomad_chr = chro
        gnomad_pos = l.get("start") + 1
        gnomad_ref = v.get("reference_sequence", "")
        gnomad_alt = v.get("sequence", "")

        if len(gnomad_ref) == 0 or len(gnomad_alt) == 0:
            gnomad_pos -= 1
            pad_base = self.referenceBases(s_id, gnomad_pos - 1)
            gnomad_ref = f'{pad_base}{gnomad_ref}'
            gnomad_alt = f'{pad_base}{gnomad_alt}'
        gnomad_string = f'chr{gnomad_chr}-{gnomad_pos}-{gnomad_ref}-{gnomad_alt}'
        prdbug(f'gnomad_string: {gnomad_string}')

        # vrs_v = self.vrs_allele_translator.translate_from(pgxseg_l, "pgxseg", require_validation=False)
        vrs_v = self.vrs_allele_translator.translate_from(gnomad_string, "gnomad", require_validation=False)
        self.vrs_variant = decamelize(vrs_v.model_dump(exclude_none=True))

        # legacy
        self.vrs_variant["location"].update({
            "sequence_id": s_id,
            "chromosome": chro
        })
        s = self.vrs_variant["location"].get("start", 0)
        e = self.vrs_variant["location"].get("end", 0)
        l = e - s
        # TODO ... thinking about lengths
        v_i = v.get("info", {})
        v_i.update({ "version": 'VRSv2', "var_length": l })
        self.vrs_variant.update({
            "variant_internal_id": f'{s_id.replace("refseq:", "")}:{s}:{self.vrs_variant.get("state", {}).get("sequence", "")}',
            "variant_state": v_s,
            "reference_sequence": v.get("reference_sequence", ""),
            "info": v_i
        })


    # -------------------------------------------------------------------------#

    def __vrs_cnv(self):
        """
        A variant with a specified sequence as a subtype of VRS `SystemicVariation`.
        This remapping just covers the formats supported in the `bycon` environment
        but does not try to accommodate all use cases.
        """

        v = self.byc_variant
        l = v.get("location", {})
        v_s = v.get("variant_state", {})
        v_s_id = v_s.get("id", "___none___").replace(":", "_")
        s_id = l.get("sequence_id")
        chro = l.get("chromosome")
        pgxseg_l = self.__pgxseg_line().replace("\t", "::")
        
        if not (cnv_l := self.byc_variant.get("VRS_cnv_type")):
            return v

        prdbug(pgxseg_l)

        vrs_v = self.vrs_cnv_translator.translate_from(pgxseg_l, "pgxseg", copy_change=cnv_l)
        self.vrs_variant = decamelize(vrs_v.model_dump(exclude_none=True))
        # legacy
        # TODO ... thinking about lengths
        s = self.vrs_variant["location"].get("start", 0)
        e = self.vrs_variant["location"].get("end", 0)
        l = e - s
        v_i = v.get("info", {})
        v_i.update({ "version": 'VRSv2', "var_length": l })
        self.vrs_variant["location"].update({
            "sequence_id": s_id,
            "chromosome": chro
        })
        self.vrs_variant.update({
            "variant_internal_id": f'{s_id.replace("refseq:", "")}:{s}-{e}:{v_s_id}',
            "variant_state": v_s,
            "info": v_i
        })


    # -------------------------------------------------------------------------#

    def __pgxseg_line(self):
        # for p in ("sequence", "reference_sequence"):
        #     if not self.byc_variant:
        #         self.byc_variant.update({p: "."})

        line = []
        for par in self.header_cols:
            par_defs = self.variant_mappings.get(par, {})
            db_key = par_defs.get("db_key", "___undefined___")
            v = get_nested_value(self.byc_variant, db_key)
            v = RefactoredValues(par_defs).strVal(v)
            if v.lower() in ("___delete___", "__delete__", "none", "___none___", "__none__", "-"):
                v = ""
            line.append(v)
        return "\t".join(line)


    # -------------------------------------------------------------------------#

    def __vrs_adjacency(self):
        """
        A variant with a specified order as a subtype of VRS `Adjacency`.
        """

        v = self.byc_variant
        v_i = v.get("info", {})
        adjseqs = v.get("adjoined_sequences", [])

        adj_l = []
        chros = []          # to update the VRS locations by order, later
        refss = []          # to update the VRS locations by order, later
        pos_type = "end"    # canonical for simple fusions's first partner

        for l in adjseqs:
            refseq = l.get("sequence_id")
            chro = chro = self.ChroNames.chro(refseq)
            if "start" in l and "end" in l: # assignment test would fail on 0
                s = l.get("start")
                e = l.get("end")
            elif (s_l := l.get("start")):
                s, e, pos_type = min(s_l), max(s_l), "start"
            elif (e_l := l.get("end")):
                s, e, pos_type = min(e_l), max(e_l), "end"

            chros.append(chro)
            refss.append(refseq)
            adj_l.append("::".join([refseq, pos_type, f'{s},{e}']))
            pos_type = "start" # init guess for second partner

        pgxadjoined = "&&".join(adj_l).replace("refseq:", "")
        vrs_v = self.vrs_adjacency_translator.translate_from(pgxadjoined, "pgxadjoined")
        self.vrs_variant = decamelize(vrs_v.model_dump(exclude_none=True))

        for i in [0, 1]:
            self.vrs_variant["adjoined_sequences"][i].update({
                "chromosome": chros[i],
                "sequence_id": refss[i]
            })

        v_i.update({ "version": 'VRSv2' })
        self.vrs_variant.update({
            "variant_internal_id": pgxadjoined,
            "variant_state": { "id": 'SO:0000806', "label": 'fusion' },
            "info": v_i
        })


    # -------------------------------------------------------------------------#

    def __create_canonical_variant(self):
        self.byc_variant.update({"errors": []})
        self.__byc_variant_normalize_type()
        self.__byc_variant_normalize_chromosome()
        self.__byc_variant_normalize_positions()
        self.__byc_variant_normalize_sequences()
        # if not "info" in self.byc_variant:
        #     self.byc_variant.update({"info": {}})
        # self.__byc_variant_add_length()

        return

    # -------------------------------------------------------------------------#

    def __byc_variant_add_length(self):
        if not "location" in self.byc_variant:
            return
        loc = self.byc_variant.get("location", {})
        s = loc.get("start")
        e = loc.get("end")
        if type(s) is not int or type(e) is not int:
            return
        self.byc_variant["info"].update({"var_length": e - s})
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_normalize_type(self):
        vt_defs = self.variant_types
        v = self.byc_variant

        v_state = v.get("variant_state", {})
        state_id = v_state.get("id", "___none___")
        variant_type = v.get("variant_type", "___none___")

        if state_id not in vt_defs.keys():   
            state_id = self.variant_types_map.get(variant_type, "___none___")

        if (state_defs := vt_defs.get(state_id)):
            # prdbug(state_defs["variant_state"])
            v.update({
                "variant_state": state_defs["variant_state"],
                "variant_dupdel": state_defs.get("DUPDEL"),
                "variant_type": state_defs.get("variant_type"),
                "VRS_cnv_type": state_defs.get("VRS_cnv_type"),
                "VCF_symbolic_allele": state_defs.get("VCF_symbolic_allele")
            })
        else:
            v["errors"].append(f'no variant type / state could be assigned')

        self.byc_variant.update(v)


    # -------------------------------------------------------------------------#

    def __byc_variant_normalize_chromosome(self):
        if not "location" in (v := self.byc_variant):
            return

        refs_ids = self.ChroNames.allRefseqs()
        chro_ids = self.ChroNames.allChros()

        s_id = v["location"].get("sequence_id", "___none___")
        chro = v["location"].get("chromosome", "___none___")

        if s_id in refs_ids and chro in chro_ids:
            pass
        elif s_id in refs_ids and chro not in chro_ids:
            chro = self.ChroNames.chro(s_id)
            v["location"].update({"chromosome": chro})
        elif chro in chro_ids and s_id not in refs_ids:
            s_id = self.ChroNames.refseq(chro)
            v["location"].update({"sequence_id": s_id})
        else:
            v["errors"].append(f'problem with sequence_id {s_id} / chromosome {chro} match')
        self.byc_variant.update(v)


    # -------------------------------------------------------------------------#

    def __byc_variant_normalize_sequences(self):
        v = self.byc_variant
        # first legacy ...
        seq = v.get("sequence", v.get("state", {}).get("sequence", ""))
        r_seq = v.get("reference_sequence", v.get("state", {}).get("reference_sequence", ""))
        # TODO: check, normalize, default...
        state = v.get("state", {})
        state.update({"sequence": seq})
        v.update({
            "state": state,
            "reference_sequence": r_seq        
        })

        self.byc_variant.update(v)


    # -------------------------------------------------------------------------#

    def __byc_variant_normalize_positions(self):
        v = self.byc_variant
        if not "location" in v:
            # HACK for adjacency
            return
        # TODO: rethink length calculation (e.g. indel...)
        if not v["location"].get("end"):
            v["location"].update({"end": int(v["location"].get("start")) + len(v.get("sequence", ""))})
        self.byc_variant.update(v)

