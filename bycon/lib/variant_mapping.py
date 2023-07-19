from datatable_utils import get_nested_value

################################################################################
################################################################################
################################################################################

class ByconVariant:

    def __init__(self, byc, variant, flavour="string"):

        self.byc = byc
        self.var_input = variant
        self.var_flavour = flavour
        self.byc_variant = {}
        self.pgx_variant = {}
        self.vrs_variant = {}
        self.pgxseg_variant = {}

        d_m = self.byc.get("datatable_mappings", {})
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


        return self.pgx_variant

    # -------------------------------------------------------------------------#
    # ----------------------------- private -----------------------------------#
    # -------------------------------------------------------------------------#

    def __create_canonical_variant(self):

    	if self.flavour == "bycon":
    		self.byc_variant = self.var_input
    		return

    	if self.flavour == "progenetix":
    		self.__byc_variant_from_progenetix()
    		return

    # -------------------------------------------------------------------------#

    def __byc_variant_from_progenetix(self):

        p_v = self.var_input

        b_v = {}
        for p_k, p_d in self.variant_mappings.items():
            dotted_value = p_d.get(db_key)
            parameter_type = p_d.get("type", "string")
            if not dotted_value:
                continue
            v = get_nested_value(p_v, dotted_value, parameter_type)
            b_v.update({p_k: v})
        self.byc_variant.update(b_v)
        return

  	
