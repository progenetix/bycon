from uuid import uuid4
from pymongo import MongoClient
from os import environ

from config import *
from bycon_helpers import prdbug, prjsonnice, test_truthy
from query_generation import ByconQuery


################################################################################

def execute_bycon_queries(ds_id, BQ, byc):
    """podmd
    
    Pre-configured queries are performed in an aggregation pipeline against
    the standard "Progenetix"-type MongoDB collections.
        
    podmd"""

    # TODO: a new type, where we use query aggregation for multiple
    # variants observed in the same biosample to get aggregated; _i.e._ 
    # different from a AND query for variants which would require the variant
    # to fulfill both conditions

    h_o_methods = byc["handover_definitions"]["h->o_methods"]
    r_e_id = str(byc.get("response_entity_id", "___none___"))

    exe_queries = {}
    if "dataset_results" not in byc.keys():
        byc.update({"dataset_results": {}})

    data_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    data_db = data_client[ds_id]
    data_collnames = data_db.list_collection_names()

    q_e_s = BQ.get("entities", {})
    v_i_q = BQ.get("variant_id_query")
    for q_e, q_o in q_e_s.items():
        collname = q_o.get("collection", "___none___")
        q = q_o.get("query")
        if q:
            exe_queries.update({collname: q})

    byc.update({"queries_at_execution": exe_queries})
    if not byc.get("original_queries"):
        byc.update({"original_queries": exe_queries})

    # collection of results
    prefetch = {}
    prevars = {
        "ds_id": ds_id,
        "data_db": data_db,
        "original_queries": byc.get("original_queries", {}),
        "pref_m": "",
        "h_o_def": {},
        "query": {}
    }

    ############################################################################

    prdbug(f'queries at execution:')
    prdbug(exe_queries)

    if not exe_queries.keys():
        return prefetch

    ############################################################################

    """podmd
    
    All queries are aggregated towards biosamples.
        
    podmd"""

    biosamples_query = exe_queries.get("biosamples", False)
    if biosamples_query:
        pref_k = "biosamples.id"
        prevars.update({
            "pref_m": pref_k,
            "query": biosamples_query,
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})

    individuals_query = exe_queries.get("individuals", False)
    if individuals_query:
        pref_k = "individuals.id"
        prevars.update({
            "pref_m": pref_k,
            "query": individuals_query,
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})

        pref_vs = prefetch["individuals.id"]["target_values"]

        pref_k = "biosamples.id"
        prevars.update({
            "pref_m": pref_k,
            "query": {"individual_id": {'$in': pref_vs}},
            "h_o_def": h_o_methods.get(pref_k)
        })
        biosids_from_indq = _prefetch_data(prevars)

        if "biosamples.id" in prefetch:
            bsids = list(set(biosids_from_indq["target_values"]) & set(prefetch["biosamples.id"]["target_values"]))
            prefetch["biosamples.id"].update({"target_values": bsids, "target_count": len(bsids)})
        else:
            prefetch["biosamples.id"] = biosids_from_indq

    callsets_query = exe_queries.get("analyses", False)
    if callsets_query:     
        # since analyses contain biosample_id no double calling is required
        pref_k = "analyses.biosample_id->biosamples.id"
        prevars.update({
            "pref_m": pref_k,
            "query": callsets_query,
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})

        if "biosamples.id" in prefetch.keys():
            bsids = list(set(prefetch[pref_k]["target_values"]) & set(
                prefetch["biosamples.id"]["target_values"]))
            prefetch["biosamples.id"].update({"target_values": bsids, "target_count": len(bsids)})
        else:
            prefetch["biosamples.id"] = prefetch[pref_k]

    variants_query = exe_queries.get("variants")
    if not variants_query:
        if "genomicVariant" in r_e_id and "biosamples.id" in prefetch.keys():
            variants_query = {"biosample_id": {'$in': prefetch["biosamples.id"].get("target_values", ["___none___"])}}

    if variants_query:
        """podmd
        ### `variants` Query and Aggregation

        1. If a `variants` query exists (i.e. has been defined in `exe_queries`), in a first pass
        all `biosample_id` values are retrieved.
        2. If already a `"biosamples.id"` result exists (e.g. from a biosample query), the lists
        of callset `id` values from the different queries are intersected. Otherwise, the analyses
        from the variants query are the final ones.
        3. Since so far not all matching variants have been retrieved (only the biosamples which
        contain them), they are now fetched using the original query or a combination of the
        original query and the matching biosamples from the intersect.
        podmd"""

        if type(variants_query) is not list:
            variants_query = [variants_query]

        v_q_l = variants_query.copy()

        pref_k = "variants.biosample_id->biosamples.id"
        prevars.update({
            "pref_m": pref_k,
            "query": v_q_l.pop(0),
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})

        if "biosamples.id" in prefetch.keys():
            bsids = list(set(prefetch["biosamples.id"]["target_values"]) & set(
                prefetch[pref_k]["target_values"]))
            prefetch["biosamples.id"].update({"target_values": bsids, "target_count": len(bsids)})
            # variants_query = [{"$and": [variants_query[0], {"biosample_id": {"$in": bsids}}]}]
        else:
            prefetch["biosamples.id"] = prefetch[pref_k]

        # if there are more than 1 variant query, intersect the biosample_ids from
        # the previous queries (_i.e._ all variants have to occurr in the same biosample)
        if len(v_q_l) > 0:
            for v_q in v_q_l:
                v_bsids = prefetch["biosamples.id"]["target_values"]
                prdbug(f'before {prefetch["biosamples.id"]["target_count"]}')
                if (len(v_bsids) == 0):
                    break
                v_q = {"$and": [v_q, {"biosample_id": {"$in": v_bsids}}]}
                prevars.update({
                    "pref_m": pref_k,
                    "query": v_q,
                    "h_o_def": h_o_methods.get(pref_k)
                })
                prefetch.update({pref_k: _prefetch_data(prevars)})
                prefetch["biosamples.id"] = prefetch[pref_k]
                prdbug(f'after {prefetch["biosamples.id"]["target_count"]}')

        # collect variants from the multi match
        # here we can use the $or query since the requirement (all variant results
        # have to intersect for the same biosamples) has been met
        pref_k = "variants._id"
        if len(variants_query) > 1:
            v_v_q = {"$or": variants_query}
        else:
            v_v_q = variants_query[0]
        if len(prefetch["biosamples.id"]["target_values"]) > 0:
            v_v_q = {"$and": [v_v_q, {"biosample_id": {"$in": prefetch["biosamples.id"]["target_values"]}}]}
        else:
            # fallback for 0 match results
            v_v_q = {"$and": [v_v_q, {"biosample_id": {"$in": ["___undefined___"]}}]}

        prevars.update({
            "pref_m": pref_k,
            "query": v_v_q,
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})

        # prevars["pref_m"] = "variants.variant_internal_id"
        # prevars["query"] = {"_id": {"$in": prefetch["variants._id"]["target_values"]}}
        # prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})

    elif v_i_q:
        pref_k = "variants._id"
        prevars.update({
            "pref_m": pref_k,
            "query": v_i_q,
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})
        
        # prevars["pref_m"] = "variants.variant_internal_id"
        # prevars["query"] = {"_id": {"$in": prefetch["variants._id"]["target_values"]}}
        # prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})


    ############################################################################
    """podmd
    ### Result Aggregation

    The above queries have provided `biosamples.id` values which now are used to retrieve the
    matching final biosample and callset `_id` values.

    For variants the `_id` values only exist if a variants query had been performed.
    In that case no separate recall has to be performed since a biosample intersection
    had been performed already (to limit the _a priori_ variant response).

    If no variant query was performed _but_ the response asks for variants => all
    callset variants will be returned.

    TODO: Benchmark if the `_id` retrieval & storage speeds up biosample and callset recovery
    in handover scenarios or if `id` is fine.

    TODO: The return-driven query selection will need to be refined; queries can
    potentially lead to huge responses here...
    podmd"""

    if "biosamples.id" not in prefetch:
        pref_k = "biosamples.id"
        prevars.update({
            "pref_m": pref_k,
            "query": {"id": "___undefined___"},
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})
        # prefetch.update({"biosamples.id": {**h_o_methods.get("biosamples.id")}})
        # prefetch["biosamples.id"].update({
        #     "id": str(uuid4()),
        #     "source_db": ds_id,
        #     "target_values": [],
        #     "target_count": 0
        # })

        byc["dataset_results"].update({ds_id: prefetch})
        return

    pref_k = "analyses._id"
    prevars.update({
        "pref_m": pref_k,
        "query": {"biosample_id": {"$in": prefetch["biosamples.id"]["target_values"]}},
        "h_o_def": h_o_methods.get(pref_k)
    })
    prefetch.update({pref_k: _prefetch_data(prevars)})

    pref_k = "biosamples._id"
    prevars.update({
        "pref_m": pref_k,
        "query": {"id": {"$in": prefetch["biosamples.id"]["target_values"]}},
        "h_o_def": h_o_methods.get(pref_k)
    })
    prefetch.update({pref_k: _prefetch_data(prevars)})

    # TODO: have this checked... somewhere else based on the response_entity_id
    if "individual" in r_e_id or "phenopacket" in r_e_id:
        pref_k = "biosamples.individual_id->individuals.id"
        prevars.update({
            "pref_m": pref_k,
            "query": {"_id": {"$in": prefetch["biosamples._id"]["target_values"]}},
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})

        pref_k = "individuals._id"
        prevars.update({
            "pref_m": pref_k,
            "query": {"id": {"$in": prefetch["biosamples.individual_id->individuals.id"]["target_values"]}},
            "h_o_def": h_o_methods.get(pref_k)
        })
        prefetch.update({pref_k: _prefetch_data(prevars)})

    ############################################################################

    data_client.close()
    byc["dataset_results"].update({ds_id: prefetch})

    try:
        prdbug(f'{ds_id} biosample count after queries: {prefetch["biosamples._id"]["target_count"]}')
    except:
        pass

    return prefetch


################################################################################

def _prefetch_data(prevars):
    """podmd
    The prefetch pref_m queries the specified collection `source_collection` of
    the `data_db` with the provided query, and stores the distinct values of the
    `source_key` as `target_values`.

    The results may reference across collections. A typical example here would be
    to retrieve `biosample_id` values from the `variants` collection to point
    to `id` values in the `biosamples` collection.

    These "handover" objects can then be stored and used to retrieve values of
    previous queries for procedural use or second-pass data retrieval.

    podmd"""

    pref_m = prevars["pref_m"]
    data_db = prevars["data_db"]
    h_o_def = prevars["h_o_def"]
    # prdbug(pref_m)
    # prdbug(prevars["query"])
    dist = data_db[h_o_def["source_collection"]].distinct(h_o_def["source_key"], prevars["query"])
    h_o = {**h_o_def}
    t_v_s = dist if dist else []
    h_o.update(
        {
            "id": str(uuid4()),
            "source_db": prevars["ds_id"],
            "target_values": t_v_s,
            "target_count": len(t_v_s),
            "original_queries": prevars.get("original_queries", None)
        }
    )
    return h_o


################################################################################
