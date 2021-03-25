import json
from pymongo import MongoClient
from bson.objectid import ObjectId
from os import path, pardir
import sys

from cgi_utils import *

################################################################################

def retrieve_variants(ds_id, r, byc):

    vs = [ ]

    mongo_client = MongoClient()
    v_coll = mongo_client[ ds_id ][ "variants" ]
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]

    if not byc["method"] in byc["these_prefs"]["all_variants_methods"]:
        if "vs._id" in byc["query_results"]:
            for v in v_coll.find({"_id": { "$in": byc["query_results"]["vs._id"]["target_values"] } }):
                vs.append(v)
            return vs
        else:
            return vs

    ############################################################################

    for bs_id in byc["query_results"]["bs.id"][ "target_values" ]:
        for v in v_coll.find(
                {"biosample_id": bs_id },
                { "_id": 0, "assembly_id": 0, "digest": 0, "callset_id": 0 }
        ):
            v["log2"] = False
            if "info" in v:
                if "cnv_value" in v["info"]:
                    if isinstance(v["info"]["cnv_value"],float):
                        v["log2"] = round(v["info"]["cnv_value"], 3)
            v["start"] = int(v["start"])
            v["end"] = int(v["end"])
            if v["log2"] == False:
                del(v["log2"])
            if "info" in v:
                del(v["info"])
            vs.append(v)

    return vs

