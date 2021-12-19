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

    v["log2"] = False
    if "info" in v:
        if "cnv_value" in v["info"]:
            if isinstance(v["info"]["cnv_value"],float):
                v["log2"] = round(v["info"]["cnv_value"], 3)
        if not "info" in drop_fields:
            drop_fields.append("info")

    if v["log2"] == False:
        if "variant_type" in v:
            if v["variant_type"] in byc["variant_definitions"]["cnv_dummy_values"].keys():
                v["log2"] = byc["variant_definitions"]["cnv_dummy_values"][ v["variant_type"] ]

    if v["log2"] == False:
        drop_fields.append("log2")

    v["start"] = int(v["start"])
    v["end"] = int(v["end"])

    for d_f in drop_fields:   
        v.pop(d_f, None)

    return v

################################################################################





