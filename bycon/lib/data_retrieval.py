from pymongo import MongoClient
from os import environ

################################################################################

def retrieve_data(ds_id, byc):

    r_c = byc["response_entity"]["collection"]
    r_k = r_c+"_id"

    r_s_res = []

    for r_t, r_d in byc["beacon_defaults"]["entity_defaults"].items():
        r_t_k = r_d.get("h->o_access_key")
        if not r_t_k:
            continue

        if r_d["response_entity_id"] == byc["response_entity_id"]:
            r_k = r_d["h->o_access_key"]

    if "variants" in r_c:
        return retrieve_variants(ds_id, byc)

    ds_results = byc["dataset_results"][ds_id]
    if r_k not in ds_results.keys():
        return r_s_res

    res = byc["dataset_results"][ds_id][r_k]
    q_k = res.get("target_key", "_id")
    q_v_s = res.get("target_values", [])
    q_db = res.get("source_db", "___none___")
    q_coll = res.get("target_collection", "___none___")

    mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    data_coll = mongo_client[ q_db ][ q_coll ]

    for q_v in q_v_s:
        o = data_coll.find_one({q_k: q_v })
        r_s_res.append(o)

    return r_s_res

################################################################################

def retrieve_variants(ds_id, byc):

    ds_results = byc["dataset_results"][ds_id]

    mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    data_db = mongo_client[ ds_id ]
    v_coll = mongo_client[ ds_id ][ "variants" ]

    r_s_res = []

    if "variants._id" in ds_results:
        for v_id in ds_results["variants._id"]["target_values"]:
            v = v_coll.find_one({"_id":v_id})
            r_s_res.append(v)
        return r_s_res
    elif "variants.variant_internal_id" in ds_results:
        for v_id in ds_results["variants.variant_internal_id"]["target_values"]:
            vs = v_coll.find({"variant_internal_id":v_id})
            for v in vs:
                r_s_res.append(v)
        return r_s_res

    return False
