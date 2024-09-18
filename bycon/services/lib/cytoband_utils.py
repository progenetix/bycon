import csv, datetime, re, time, base36, yaml
from os import environ, path, pardir

from bycon import BYC, bands_from_cytobands, generate_id, ByconVariant, ChroNames

################################################################################
################################################################################
################################################################################

def variants_from_revish(bs_id, cs_id, technique, iscn):
    v_s, v_e = deparse_ISCN_to_variants(iscn)
    variants = []

    # the id here is a placeholder since we now use a stringified version of the
    # MongoDB ObjectId w/ `pgxvar-` prepend
    for v in v_s:

        v.update({
            "id": generate_id("pgxvar"),
            "biosample_id": bs_id,
            "analysis_id": cs_id,
            "updated": datetime.datetime.now().isoformat()
        })

        variants.append(ByconVariant().byconVariant(v))

    return variants, v_e


################################################################################

def deparse_ISCN_to_variants(iscn):
    argdefs = BYC.get("argument_definitions", {})
    chro_names = ChroNames()
    i_d = BYC["interval_definitions"]
    v_t_defs = BYC.get("variant_type_definitions")

    iscn = "".join(iscn.split())
    variants = []
    cb_pat = re.compile( argdefs["cyto_bands"]["pattern"] )
    errors = []

    for cnv_t, cnv_defs in v_t_defs.items():
        revish = cnv_defs.get("revish_label")
        if not revish:
            continue

        iscn_re = re.compile(rf"^.*?{revish}\(([\w.,]+)\).*?$", re.IGNORECASE)
        if iscn_re.match(iscn):
            m = iscn_re.match(iscn).group(1)
            for i_v in re.split(",", m):               
                if not cb_pat.match(i_v):
                    continue
                cytoBands, chro, start, end, error = bands_from_cytobands(i_v)
                if len(error) > 0:
                    errors.append(error)
                    continue
                v_l = end - start
                cytostring = "{}({})".format(cnv_t, i_v).lower()
                if "amp" in revish and v_l > i_d.get("cnv_amp_max_size", 3000000):
                    revish = "hldup"
                v_s = {}              
                v = ({
                    "variant_state": cnv_defs.get("variant_state"),
                    "location": {
                        "sequence_id": chro_names.refseq(chro),
                        "chromosome": chro,
                        "start": start,
                        "end": end
                    },
                    "info": {
                        "ISCN": cytostring,
                        "var_length": v_l,
                        "cnv_value": cnv_defs.get("cnv_dummy_value"),
                        "note": "from text annotation; CNV dummy value"
                    }
                })

                variants.append(v)

    return variants, " :: ".join(errors)


