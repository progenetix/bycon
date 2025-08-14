import re
from copy import deepcopy
from deepmerge import always_merger

from ga4gh.vrs.dataproxy import create_dataproxy
from ga4gh.vrs.extras.translator import AlleleTranslator, CnvTranslator


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
        self.byc_variant = {}
        self.pgx_variant = {}
        self.vrs_variant = {}
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
        self.vrs_allele = ByconSchemas("VRSallele", "").get_schema_instance()
        self.vrs_cnv = ByconSchemas("VRScopyNumberChange", "").get_schema_instance()
        self.vrs_adjacency = ByconSchemas("VRSadjacency", "").get_schema_instance()
        self.pgx_variant = ByconSchemas("pgxVariant", "").get_schema_instance()

        seqrepo_rest_service_url = 'seqrepo+file:///Users/Shared/seqrepo/2024-12-20'
        seqrepo_dataproxy = create_dataproxy(uri=seqrepo_rest_service_url)
        self.translator = AlleleTranslator(data_proxy=seqrepo_dataproxy)
        self.cnv_translator = CnvTranslator(data_proxy=seqrepo_dataproxy)


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def byconVariant(self, variant={}):
        self.byc_variant = variant
        self.__create_canonical_variant()
        return self.byc_variant


    # -------------------------------------------------------------------------#

    def pgxVariant(self, variant=None):

        if not variant:
            return self.pgx_variant
        self.byc_variant = variant
        self.__create_canonical_variant()
        var_keys = list(self.pgx_variant.keys())
        for p_k, p_d in self.byc_variant.items():
            if p_k in var_keys:
                self.pgx_variant.update({p_k: p_d})
        for pgx_k in var_keys:
            if not self.pgx_variant.get(pgx_k):
                self.pgx_variant.pop(pgx_k, None)
        if "adjoined_sequences" in self.byc_variant.keys():
            self.pgx_variant.pop("location", None)
        else:
            self.pgx_variant.pop("adjoined_sequences", None)
        self.pgx_variant.pop("variant_type", None)
        return self.pgx_variant


    # -------------------------------------------------------------------------#

    def vcfVariant(self, variant={}):
        """
        Mapping of the relevant variant parameters into an object with

        * standard VCF column headers such as as `#CHROM` as keys
        * an `INFO` key + string for CNVs
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
            "ALT": v.get("sequence", ""),
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
        state_id = self.byc_variant["variant_state"].get("id", "___none___")
        state_defs = vt_defs.get(state_id, {})
        vrs_type = state_defs.get("VRS_type", "___none___")

        if "Allele" in str(vrs_type):
            vrs_v = self.__vrs_allele()
        elif "Adjacency" in str(vrs_type):
            vrs_v = self.__vrs_adjacency()
        else:
            vrs_v = self.__vrs_cnv()

        # TODO: since the vrs_variant has been created as a new object we now
        #       add the annotation fields back (should empties be omitted?)
        for v_s in ("biosample_id", "analysis_id"): # "id", "variant_internal_id"
            if (v_v := self.byc_variant.get(v_s)):
                vrs_v.update({v_s: v_v})
        if len(v_a := self.byc_variant.get("variant_alternative_ids", [])) > 0:
            vrs_v.update({"variant_alternative_ids": v_a})
        for v_o in ("identifiers", "molecular_attributes", "variant_level_data"): # "info",
            if (v_v := self.byc_variant.get(v_o)):
                vrs_v.update({v_o: v_v})

        self.vrs_variant.update(vrs_v)
        return self.vrs_variant


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
        spdi = f'{s_id.replace("refseq:", "")}:{l.get("start")}:{v.get("reference_sequence", "")}:{v.get("sequence", "")}'.replace(":None", ":")

        vrs_v = self.translator.translate_from(spdi, "spdi", require_validation=False)
        vrs_v = vrs_v.model_dump(exclude_none=True)

        # legacy
        vrs_v["location"].update({
            "sequence_id": s_id,
            "chromosome": chro
        })
        s = vrs_v["location"].get("start", 0)
        e = vrs_v["location"].get("end", 0)
        l = e - s
        # TODO ... thinking about lengths
        vrs_v.update({
            "variant_internal_id": spdi,
            "variant_state": v_s,
            "info": { "version": 'VRSv2', "var_length": l }
        })

        return vrs_v


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
        pgxseg_l = self.__pgxseg_line()
        
        if not (cnv_l := self.byc_variant.get("VRS_cnv_type")):
            return v
        cnv_i = self.byc_variant.get("variant_state", {}).get("id", None)
        vrs_v = self.cnv_translator.translate_from(pgxseg_l, "pgxseg", copy_change=cnv_l)
        vrs_v = vrs_v.model_dump(exclude_none=True)
        # legacy
        vrs_v["location"].update({
            "sequence_id": s_id,
            "chromosome": chro
        })
        s = vrs_v["location"].get("start", 0)
        e = vrs_v["location"].get("end", 0)
        l = e - s
        # TODO ... thinking about lengths
        vrs_v.update({
            "variant_internal_id": f'{s_id.replace("refseq:", "")}:{s}-{e}:{v_s_id}',
            "variant_state": v_s,
            "info": { "version": 'VRSv2', "var_length": l }
        })

        return vrs_v


    # -------------------------------------------------------------------------#


    def __pgxseg_line(self):
        for p in ("sequence", "reference_sequence"):
            if not self.byc_variant:
                self.byc_variant.update({p: "."})

        line = []
        for par in self.header_cols:
            par_defs = self.variant_mappings.get(par, {})
            db_key = par_defs.get("db_key", "___undefined___")
            v = get_nested_value(self.byc_variant, db_key)
            v = RefactoredValues(par_defs).strVal(v)
            line.append(v)
        return "\t".join(line)

    # -------------------------------------------------------------------------#

    def __vrs_adjacency(self):
        """
        A variant with a specified order as a subtype of VRS `Adjacency`.
        """

        vt_defs = self.variant_types
        v = self.byc_variant

        s_i = []
        a_s = v.get("adjoined_sequences", [])
        for a_i, a_l in enumerate(a_s):
            l = self.__vrs_location({"location": a_l})
            if a_i == 0:
                l.update({
                    "end": [l["start"], l["end"]]
                })
                l.pop("start", None)
            else:
                l.update({
                    "start": [l["start"], l["end"]]
                })
                l.pop("end", None)                
            s_i.append(l)

        vrs_v = deepcopy(self.vrs_adjacency)
        vrs_v.update({
            "adjoined_sequences": s_i,
            "type": "Adjacency"
        })

        return vrs_v

    # -------------------------------------------------------------------------#

    def __vrs_location(self, v):
        return {
            "type": "SequenceLocation",
            "sequenceReference": v["location"].get("sequence_id"),
            "start": v["location"].get("start"),
            "end": v["location"].get("end")
        }


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __create_canonical_variant(self):
        self.byc_variant.update({"errors": []})
        self.__byc_variant_normalize_type()
        self.__byc_variant_normalize_chromosome()
        self.__byc_variant_normalize_positions()
        self.__byc_variant_normalize_sequences()
        self.__byc_variant_add_digest()
        self.__byc_variant_add_adjacency_digest()
        if not "info" in self.byc_variant:
            self.byc_variant.update({"info": {}})
        self.__byc_variant_add_length()

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

        if state_id in vt_defs.keys():
            state_defs = vt_defs[state_id]
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
        return


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
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_normalize_sequences(self):
        v = self.byc_variant
        seq = v.get("sequence", v.get("alternate_bases"))
        r_seq = v.get("reference_sequence", "")
        # TODO: check, normalize, default...
        v.update({
            "sequence": seq,
            "reference_sequence": r_seq        
        })

        self.byc_variant.update(v)
        return


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
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_add_digest(self):
        v = self.byc_variant
        if not "location" in v:
            return
        seq_re = '^[ACGTN]+$'  
        v_lab = v["variant_state"].get("id", "___NA___").replace(":", "_")
        v_seqid = v["location"].get("chromosome", "___NA___")
        seq = v.get("sequence", "")
        rseq = v.get("reference_sequence", "")

        if re.match(f'{seq_re}', str(seq)) or re.match(f'{seq_re}', str(rseq)):
            v_lab = f'{rseq}>{seq}'
        v.update({"variant_internal_id": f'{v_seqid}:{v["location"]["start"]}-{v["location"]["end"]}:{v_lab}'})

        self.byc_variant.update(v)
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_add_adjacency_digest(self):
        v = self.byc_variant
        if not "adjoined_sequences" in v:
            return
        v_lab = v["variant_state"].get("id", "___NA___").replace(":", "_")
        a = v.get("adjoined_sequences", [])
        if len(a) < 2:
            return
        a_1 = a[0]
        a_2 = a[1]
        d = f'{a_1.get("chromosome", "___NA___")}:{a_1["start"]}-{a_1["end"]}::{a_2.get("chromosome", "___NA___")}:{a_2["start"]}-{a_2["end"]}:{v_lab}'
        self.byc_variant.update({"variant_internal_id": d})
        for p in ["sequence", "reference_sequence", "location"]:
            self.byc_variant.pop(p, None)
        return


