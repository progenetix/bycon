from pymongo import MongoClient

################################################################################

def retrieve_data(ds_id, byc):

    r_c = byc["response_entity"]["collection"]
    r_k = r_c+"_id"

    for r_t, r_d in byc["beacon_mappings"]["response_types"].items():
        # print(r_d["entity_type"], byc["response_entity_id"])

        if r_d["entity_type"] == byc["response_entity_id"]:
            r_k = r_d["h->o_access_key"]

    if "variants" in r_c:
        r_s_res = retrieve_variants(ds_id, byc)
        return r_s_res

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    data_coll = mongo_client[ ds_id ][ r_c ]

    ds_results = byc["dataset_results"][ds_id]

    if r_k in ds_results:
        r_s_res = []
        for d in data_coll.find({"_id":{"$in": ds_results[ r_k ]["target_values"] }}):
            r_s_res.append(d)

        return r_s_res

    return []

################################################################################

def retrieve_variants(ds_id, byc):

    ds_results = byc["dataset_results"][ds_id]

    if "all_variants_methods" in byc["service_config"]:
        if byc["method"] in byc["service_config"]["all_variants_methods"]:
            return False

    mongo_client = MongoClient()
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
