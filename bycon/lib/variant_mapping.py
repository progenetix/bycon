import re
from copy import deepcopy
from deepmerge import always_merger

from cgi_parsing import prdbug
from config import *
from bycon_helpers import assign_nested_value, get_nested_value
from schema_parsing import object_instance_from_schema_name
from genome_utils import ChroNames

################################################################################
################################################################################
################################################################################

class ByconVariant:

    def __init__(self, byc, variant={}):
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
        self.variant_types = byc.get("variant_type_definitions", {})

        t_states = {}
        for v_t, v_d in self.variant_types.items():
            t_states.update({v_d["variant_type"]: v_d["variant_type_id"]})
        self.variant_types_map = t_states

        # datatable mappings contain the "name to place in object" definitions
        # these are in essence identical to the `db_key` mappings in
        # `argument_definitions` but logically different (query vs. defiition; `default`...)
        d_m = BYC["datatable_mappings"].get("definitions", {})
        d_m_v = d_m.get("genomicVariant", {})
        self.variant_mappings = d_m_v.get("parameters", {})
        self.vrs_allele = object_instance_from_schema_name("VRSallele", "")
        self.vrs_cnv = object_instance_from_schema_name("VRScopyNumberChange", "")


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def byconVariant(self, variant={}):
        self.byc_variant = variant
        self.__create_canonical_variant()
        return self.byc_variant


    # -------------------------------------------------------------------------#

    def pgxVariant(self, variant={}):
        self.byc_variant = variant
        self.__create_canonical_variant()
        b_v = self.byc_variant
        p_v = {} # to do: pgx cb variant instance
        for p_k, p_d in self.variant_mappings.items():
            dotted_key = p_d.get("db_key")
            i_v = b_v.get(p_k)
            if not dotted_key:
                continue
            assign_nested_value(p_v, dotted_key, i_v, p_d)

        self.pgx_variant.update(p_v) 
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

        v_l = v.get("variant_length", 1)
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
        # prdbug(self.byc_variant)
        self.__create_canonical_variant()
        # prdbug(self.byc_variant)

        vt_defs = self.variant_types
        state_id = self.byc_variant["variant_state"].get("id", "___none___")
        state_defs = vt_defs.get(state_id, {})
        vrs_type = state_defs.get("VRS_type", "___none___")

        if "Allele" in vrs_type:
            vrs_v = self.__vrs_allele()
        else:
            vrs_v = self.__vrs_cnv()

        # TODO: since the vrs_variant has been created as a new object we now
        #       add the annotation fields back (should empties be omitted?)
        for v_s in ("biosample_id", "callset_id", "id", "variant_internal_id"):
            if (v_v := self.byc_variant.get(v_s)):
                vrs_v.update({v_s: v_v})
        vrs_v.update({"variant_alternative_ids": self.byc_variant.get("variant_alternative_ids", [])})
        for v_o in ("identifiers", "info", "molecular_attributes", "variant_level_data"):
            vrs_v.update({v_o: self.byc_variant.get(v_o, {})})

        self.vrs_variant.update(vrs_v)
        return self.vrs_variant


    # -------------------------------------------------------------------------#

    def __vrs_allele(self):
        """
        A variant with a specified sequence as a subtype of VRS `MolecularVariation`.
        This remapping just covers the formats supported in the `bycon` environment
        but does not try to accommodate all use cases.
        """
        vt_defs = self.variant_types
        v = self.byc_variant
        vrs_a = deepcopy(self.vrs_allele)
        vrs_v = {
            "state": {
                "sequence": v.get("sequence")
            },
            "location": {
                "sequence_id": v["location"].get("sequence_id"),
                "interval": {
                    "start": {"value": v["location"].get("start")},
                    "end": {"value": v["location"].get("end")}
                }
            }
        }
        vrs_v = always_merger.merge(vrs_a, vrs_v)

        return vrs_v


    # -------------------------------------------------------------------------#

    def __vrs_cnv(self):
        """
        A variant with a specified sequence as a subtype of VRS `SystemicVariation`.
        This remapping just covers the formats supported in the `bycon` environment
        but does not try to accommodate all use cases.
        """

        vt_defs = self.variant_types
        v = self.byc_variant

        vrs_c = deepcopy(self.vrs_cnv)
        vrs_v = {
            "copy_change": v["variant_state"].get("id", "___none___").lower(),
            "subject": {
                "sequence_id": v["location"].get("sequence_id"),
                "interval": {
                    "start": {"value": v["location"].get("start")},
                    "end": {"value": v["location"].get("end")}
                }
            },
            "type": "CopyNumberChange"
        }
        vrs_v = always_merger.merge(vrs_c, vrs_v)

        return vrs_v


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __create_canonical_variant(self):
        v = self.byc_variant
        v.update({"errors": []})
        self.__byc_variant_normalize_type()
        self.__byc_variant_normalize_chromosome()
        self.__byc_variant_normalize_positions()
        self.__byc_variant_normalize_sequences()
        self.__byc_variant_add_digest()

        if not "info" in v:
            v.update({"info": {}})

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
                "VCF_symbolic_allele": state_defs.get("VCF_symbolic_allele")
            })
        else:
            v["errors"].append(f'no variant type / state could be assigned')

        self.byc_variant.update(v)
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_normalize_chromosome(self):
        v = self.byc_variant

        refs_ids = self.ChroNames.allRefseqs()
        chro_ids = self.ChroNames.allChros()

        s_id = v["location"].get("sequence_id", "___none___")
        chro = v["location"].get("chromosome", "___none___")
        if s_id in refs_ids and chro in chro_ids:
            return

        if s_id in refs_ids and chro in chro_ids:
            pass
        elif s_id in refs_ids and chro not in chro_ids:
            chro = self.ChroNames.chro(s_id)
            v["location"].update({"chromosome": chro})
        elif chro in chro_ids and s_id not in refs_ids:
            s_id = self.ChroNames.refseq(chro)
            v["location"].update({"sequence_id": s_id})
        else:
            v["errors"].append(f'no sequence_id / chromosome could be assigned')

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
        if not v["location"].get("end"):
            v["location"].update({"end": int(v["location"].get("start")) + len(v.get("sequence", ""))})

        try:
            v.update({"variant_length": v["location"].get("end") - v["location"].get("start")})
        except Exception as e:
            v["errors"].append(e)

        self.byc_variant.update(v)
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_add_digest(self):
        v = self.byc_variant
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

