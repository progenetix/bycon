import json
from pymongo import MongoClient
from bson.objectid import ObjectId

from cgi_parse import *

################################################################################

def retrieve_variants_from_biosample_ids(data_db, bs_ids):

    vs = [ ]

    for bs_id in bs_ids:

        vs += retrieve_variants_for_biosample_by_biosample_id(data_db, bs_id)

    return vs

################################################################################

def retrieve_variants_for_biosample_by_biosample_id(data_db, bs_id):

    vs = [ ]

    try:
        vs = list( data_db["variants"].find({"biosample_id":bs_id}) )
    except:
        return vs

    return vs

################################################################################

def retrieve_variants_for_individual_by_individual_id(data_db, ind_id):

    vs = [ ]    

    bs_ids = data_db["biosamples"].distinct("id", {"individual_id":ind_id})

    if len(bs_ids) > 0:
        for bs_id in bs_ids:
            try:
                vs += list(data_db["variants"].find({"biosample_id":bs_id}))
            except:
                pass

        return vs

    return vs

################################################################################

def normalize_variant_values_for_export(v, byc, drop_fields=None):

    drop_fields = [] if drop_fields is None else drop_fields

    v_defs = byc["variant_definitions"]

    v["log2"] = False
    if "info" in v:
        if "cnv_value" in v["info"]:
            if isinstance(v["info"]["cnv_value"],float):
                v["log2"] = round(v["info"]["cnv_value"], 3)
        if not "info" in drop_fields:
            drop_fields.append("info")

    if v["log2"] == False:
        if "variant_type" in v:
            if v["variant_type"] in v_defs["cnv_dummy_values"].keys():
                v["log2"] = v_defs["cnv_dummy_values"][ v["variant_type"] ]

    if v["log2"] == False:
        drop_fields.append("log2")

    v["start"] = int(v["start"])
    v["end"] = int(v["end"])

    for d_f in drop_fields:   
        v.pop(d_f, None)

    return v

################################################################################

def variant_create_digest(v):

    t = "var"
    if "variant_state" in v:
        if "id" in v["variant_state"]:
            t = v["variant_state"]["id"]
            t = re.sub(":", "_", t)
    elif "variant_type" in v:
        t = v["variant_type"]

    p = str(v["start"])
    if "end" in v:
        p = p+"-"+str(v["end"])

    return ":".join( [v["reference_name"], p, t])

################################################################################

def deparse_ISCN_to_variants(iscn, technique, byc):

    iscn = "".join(iscn.split())
    variants = []
    vd = byc["variant_definitions"]
    cb_pat = re.compile( vd["parameters"]["cytoBands"]["pattern"] )
    errors = []

    for cnv_t, cnv_defs in vd["cnv_iscn_defs"].items():

        revish = cnv_defs["info"]["revish_label"]

        iscn_re = re.compile(rf"^.*?{revish}\(([\w.,]+)\).*?$", re.IGNORECASE)

        if iscn_re.match(iscn):

            m = iscn_re.match(iscn).group(1)

            for i_v in re.split(",", m):

                if not cb_pat.match(i_v):
                    continue

                cytoBands, chro, start, end, error = bands_from_cytobands(i_v, byc)
                if len(error) > 0:
                    errors.append(error)
                    continue

                v_l = end - start
                t = cnv_t
                v = cnv_defs.copy()

                if "AMP" in cnv_t and v_l > vd["amp_max_size"]:
                    t = "HLDUP"
                    v = vd["cnv_iscn_defs"][t].copy()
               
                v.update({
                    "reference_name": chro,
                    "start": start,
                    "end": end,
                    "type": "CopyNumber",
                    "info": {
                        "var_length": v_l,
                        "cnv_value": vd["cnv_dummy_values"][t],
                        "provenance": technique+" ISCN conversion"
                    }
                })

                variants.append(v)

    return variants, " :: ".join(errors)


