import re
from copy import deepcopy

from cgi_parsing import prjsonnice
from datatable_utils import assign_nested_value, get_nested_value

################################################################################
################################################################################
################################################################################

class ByconVariant:

    def __init__(self, byc, variant, flavour="progenetix"):
        """
        # Class `ByconVariant`

        The class provides methods for the conversion ofgenomic variant objects
        with slight variations in their input parameters to a "canonical" intermediary
        `byc_variant` type, and from there then map per function to other formats
        (such as the Progenetix database format, VCF or VRS).

        The class is geared towards the data we currently process through the
        Progenetix platform and does not cover some use cases outside of Progenetix
        and Beacon "common use" scenarios (as of Beacon v2 / 2023).
        """

        self.byc = byc
        self.var_input = variant
        self.var_flavour = flavour
        self.byc_variant = deepcopy(variant)
        self.pgx_variant = {}
        self.vrs_variant = {}
        self.vcf_variant = {}
        self.pgxseg_variant = {}

        d_m = byc["datatable_mappings"].get("entities", {})
        d_m_v = d_m.get("variant", {})
        self.variant_mappings = d_m_v.get("parameters", {})

        self.__create_canonical_variant()


    # -------------------------------------------------------------------------#
    # ----------------------------- public ------------------------------------#
    # -------------------------------------------------------------------------#

    def byconVariant(self):
        return self.byc_variant


    # -------------------------------------------------------------------------#

    def pgxVariant(self):

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

    def vcfVariant(self):
        """
        Mapping of the relevant variant parameters into an object with

        * standard VCF column headers such as as `#CHROM` as keys
        * an `INFO` key + string for CNVs
        """

        vt_defs = self.byc.get("variant_type_definitions", {})
        b_v = self.byc_variant

        # TODO: VCF schema in some config file...
        v_v = {
            "#CHROM": b_v.get("reference_name", "."),
            "POS": int(b_v.get("start", 0)) + 1,
            "ID": ".",
            "REF": b_v.get("reference_bases", "."),
            "ALT": b_v.get("alternate_bases", ""),
            "QUAL": ".",
            "FILTER": "PASS",
            "FORMAT": "GT",
            "INFO": ""
        }

        if len(v_v["REF"]) < 1:
             v_v.update({"REF": "."})

        v_s_id = b_v.get("variant_state_id", "___none___")
        # print(v_s_id) # DEBUG
        if v_s_id in vt_defs.keys():
            s_a = vt_defs[v_s_id].get("VCF_symbolic_allele")
            # print(f'{v_s_id} - {s_a} - {v_v["ALT"]}')
            if s_a and len(v_v["ALT"]) < 1:
                v_v.update({"ALT": s_a})

        v_l = b_v.get("variant_length", 1)
        if type(v_l) is int:
            if v_l >= 50:
                v_v.update({"INFO": f'IMPRECISE;SVCLAIM=D;END={b_v.get("end")};SVLEN={v_l}'})

        self.vcf_variant.update(v_v) 
        return self.vcf_variant

    # -------------------------------------------------------------------------#

    def vrsVariant(self):
        """
        Mapping of the relevant variant parameters into a VRS object
        ... TODO ...
        """

        vt_defs = self.byc.get("variant_type_definitions", {})
        b_v = self.byc_variant

        vrs_v = {



        }

        self.vrs_variant.update(vrs_v) 
        return self.vrs_variant


    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __create_canonical_variant(self):
        vt_defs = self.byc.get("variant_type_definitions", {})
        g_aliases = self.byc.get("genome_aliases", {})

        v = self.byc_variant
        v.update({"errors": []})

        self.__byc_variant_normalize_type()
        self.__byc_variant_normalize_chromosome()
        self.__byc_variant_normalize_positions()
        self.__byc_variant_add_digest()

        if not "info" in v:
            v.update({"info": {}})

        v.pop("variant_state", None)
        v.pop("location", None)

        if self.byc["debug_mode"] is True:
            prjsonnice(v)

        return


    # -------------------------------------------------------------------------#

    def __byc_variant_normalize_type(self):
        vt_defs = self.byc.get("variant_type_definitions", {})
        v = self.byc_variant

        state_id = v.get("variant_state_id", "___none___")
        variant_type = v.get("variant_type", "___none___")
        if state_id not in vt_defs.keys():
            if "variant_state" in v:
                state_id = v["variant_state"].get("id", "___none___")

        if state_id not in vt_defs.keys():   
            if variant_type:
                for vt, vt_d in vt_defs.items():
                    dupdel = vt_d.get("DUPDEL", "___NA___")
                    tvt = vt_d.get("variant_type", "___NA___")
                    if dupdel == variant_type:
                        state_id = vt_d.get("dupdel_state_id")
                        if state_id in vt_defs.keys():
                            continue
                    elif tvt == variant_type:
                        state_id = vt_d.get("snv_state_id")
                        if state_id in vt_defs.keys():
                            continue

        if state_id in vt_defs.keys():
            state_defs = vt_defs[state_id]

            v.update({
                "variant_state_id": state_id,
                "variant_state_label": state_defs["variant_state"].get("label"),
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
        g_aliases = self.byc.get("genome_aliases", {})
        v = self.byc_variant

        refs_ids = g_aliases.get("refseq_chronames", {}).keys()
        chro_ids = g_aliases.get("chro_refseq_ids", {}).keys()

        s_id = v.get("sequence_id", "___none___")
        chro = v.get("reference_name", "___none___")
        if s_id in refs_ids and chro in chro_ids:
            return

        # alternativ input parameters
        if s_id not in refs_ids:
            if "location" in v:
                s_id = v["location"].get("sequence_id", "___none___")

        if chro not in chro_ids:
            if "location" in v:
                chro = v["location"].get("chromosome", "___none___")

        if s_id in refs_ids and chro not in chro_ids:
            c_a_s = g_aliases.get("chro_aliases", {})
            chro = c_a_s.get(s_id, "___none___")
        elif chro in chro_ids and s_id not in refs_ids:
            r_a_s = g_aliases.get("refseq_aliases", {})
            s_id = r_a_s.get(chro, "___none___")
        else:
            v["errors"].append(f'no sequence_id / chromosome could be assigned')

        v.update({
            "reference_name": chro,
            "sequence_id": s_id
        })

        self.byc_variant.update(v)
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_normalize_positions(self):
        v = self.byc_variant
        if not "start" in v and "location" in v:
            v.update({
                "start": v["location"].get("start"),
                "end": v["location"].get("end")
            })

        try:
            v.update({"variant_length": v.get("end") - v.get("start")})
        except Exception as e:
            v["errors"].append(e)

        self.byc_variant.update(v)
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_add_digest(self):
        v = self.byc_variant
       
        v_lab = v.get("variant_type")
        seq = v.get("sequence", "")
        rseq = v.get("reference_sequence", "")
        if re.match(f'\w', seq) or re.match(f'\w', rseq):
            v_lab = f'{seq}>{rseq}'
        v.update({"variant_internal_id": f'{v["reference_name"]}:{v["start"]}-{v["end"]}:{v_lab}'})

        self.byc_variant.update(v)
        return


    # -------------------------------------------------------------------------#

    def __byc_variant_from_progenetix(self):

        p_v = self.var_input

        b_v = {}
        for p_k, p_d in self.variant_mappings.items():
            dotted_key = p_d.get("db_key")
            parameter_type = p_d.get("type", "string")
            if not dotted_key:
                continue
            v = get_nested_value(p_v, dotted_key, parameter_type)
            b_v.update({p_k: v})

        info = p_v.get("info", {})
        if "info" in b_v.keys():
            for i_k, i_v in info:
                b_v["info"].update({i_k: i_v})

        self.byc_variant.update(b_v)
        return

    
