from uuid import uuid4
from pymongo import MongoClient
from os import environ
from cgi_parsing import prdbug, prjsonnice, test_truthy
from query_generation import ByconQuery


################################################################################

def execute_bycon_queries(ds_id, BQ, byc):
    """podmd
    
    Pre-configured queries are performed in an aggregation pipeline against
    the standard "Progenetix"-type MongoDB collections.
        
    podmd"""

    h_o_defs = byc["handover_definitions"]["h->o_methods"]
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
        "h_o_defs": h_o_defs,
        "original_queries": byc.get("original_queries", {}),
        "pref_m": "", "query": {}
    }

    ############################################################################

    dbm = f'queries at execution: {exe_queries}'
    prdbug(dbm, byc.get("debug_mode"))

    ############################################################################

    """podmd
    
    All queries are aggregated towards biosamples.
        
    podmd"""

    biosamples_query = exe_queries.get("biosamples", False)
    if biosamples_query:
        pref_k = "biosamples.id"
        prevars["pref_m"] = pref_k
        prevars["query"] = biosamples_query
        prefetch.update({pref_k: _prefetch_data(prevars)})

    individuals_query = exe_queries.get("individuals", False)
    if individuals_query:
        pref_k = "individuals.id"
        prevars["pref_m"] = pref_k
        prevars["query"] = individuals_query
        prefetch.update({pref_k: _prefetch_data(prevars)})

        pref_vs = prefetch["individuals.id"]["target_values"]

        pref_k = "biosamples.id"
        prevars["pref_m"] = pref_k
        prevars["query"] = {"individual_id": {'$in': pref_vs}}
        biosids_from_indq = _prefetch_data(prevars)

        if "biosamples.id" in prefetch:
            bsids = list(set(biosids_from_indq["target_values"]) & set(prefetch["biosamples.id"]["target_values"]))
            prefetch["biosamples.id"].update({"target_values": bsids, "target_count": len(bsids)})
        else:
            prefetch["biosamples.id"] = biosids_from_indq

    callsets_query = exe_queries.get("callsets", False)
    if callsets_query:
        
        # since callsets contain biosample_id no double calling is required
        prevars["pref_m"] = "callsets.biosample_id->biosamples.id"
        prevars["query"] = callsets_query
        prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})

        if "biosamples.id" in prefetch:
            bsids = list(set(prefetch["callsets.biosample_id->biosamples.id"]["target_values"]) & set(
                prefetch["biosamples.id"]["target_values"]))
            prefetch["biosamples.id"].update({"target_values": bsids, "target_count": len(bsids)})
        else:
            prefetch["biosamples.id"] = prefetch["callsets.biosample_id->biosamples.id"]

    variants_query = exe_queries.get("variants")
    if not variants_query:
        if "genomicVariant" in r_e_id:
            variants_query = {"biosample_id": {'$in': prefetch["biosamples.id"].get("target_values", [])}}

    if variants_query:

        """podmd
        ### `variants` Query and Aggregation

        1. If a `variants` query exists (i.e. has been defined in `exe_queries`), in a first pass
        all `biosample_id` values are retrieved.
        2. If already a `"biosamples.id"` result exists (e.g. from a biosample query), the lists
        of callset `id` values from the different queries are intersected. Otherwise, the callsets
        from the variants query are the final ones.
        3. Since so far not all matching variants have been retrieved (only the biosamples which
        contain them), they are now fetched using the original query or a combination of the
        original query and the matching biosamples from the intersect.
        podmd"""

        prevars["pref_m"] = "variants.biosample_id->biosamples.id"
        prevars["query"] = variants_query
        prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})

        if "biosamples.id" in prefetch.keys():
            bsids = list(set(prefetch["biosamples.id"]["target_values"]) & set(
                prefetch["variants.biosample_id->biosamples.id"]["target_values"]))
            prefetch["biosamples.id"].update({"target_values": bsids, "target_count": len(bsids)})
            variants_query = {"$and": [variants_query, {"biosample_id": {"$in": bsids}}]}
        else:
            prefetch["biosamples.id"] = prefetch["variants.biosample_id->biosamples.id"]

        prevars["pref_m"] = "variants._id"
        prevars["query"] = variants_query
        prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})

        # prevars["pref_m"] = "variants.variant_internal_id"
        # prevars["query"] = {"_id": {"$in": prefetch["variants._id"]["target_values"]}}
        # prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})

    elif v_i_q:
        prevars["pref_m"] = "variants._id"
        prevars["query"] = v_i_q
        prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})
        
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
    had been performed already (to limit the a priori variant response).

    If no variant query was performed _but_ the response asks for variants => all
    callset variants will be returned.

    TODO: Benchmark if the `_id` retrieval & storage speeds up biosample and callset recovery
    in handover scenarios or if `id` is fine.

    TODO: The return-driven query selection will need to be refined; queries can
    potentially lead to huge responses here...
    podmd"""

    if "biosamples.id" not in prefetch:
        prefetch.update({"biosamples.id": {**prevars["h_o_defs"]["biosamples.id"]}})
        prefetch["biosamples.id"].update({
            "id": str(uuid4()),
            "source_db": ds_id,
            "target_values": [],
            "target_count": 0
        })

        byc["dataset_results"].update({ds_id: prefetch})
        return

    prevars["pref_m"] = "callsets._id"
    prevars["query"] = {"biosample_id": {"$in": prefetch["biosamples.id"]["target_values"]}}
    prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})

    prevars["pref_m"] = "biosamples._id"
    prevars["query"] = {"id": {"$in": prefetch["biosamples.id"]["target_values"]}}
    prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})

    # TODO: have this checked... somewhere else based on the response_entity_id
    if "individual" in r_e_id or "phenopacket" in r_e_id:
        _prefetch_add_individuals(prevars, prefetch)

    ############################################################################

    data_client.close()

    byc["dataset_results"].update({ds_id: prefetch})

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
    h_o_defs = prevars["h_o_defs"][pref_m]

    dist = data_db[h_o_defs["source_collection"]].distinct(h_o_defs["source_key"], prevars["query"])

    h_o = {**h_o_defs}
    h_o.update(
        {
            "id": str(uuid4()),
            "source_db": prevars["ds_id"],
            "target_values": dist,
            "target_count": len(dist),
            "original_queries": prevars.get("original_queries", None)
        }
    )

    return h_o


################################################################################

def _prefetch_vars_from_biosample_loop(prevars):
    # TODO: This still allows unlimited variants, e.g. all from thousands
    # of samples and will let the server time out if too many...
    # A new paradigm is needed which includes the pagination at this step.

    pref_m = prevars["pref_m"]
    data_db = prevars["data_db"]
    h_o_defs = prevars["h_o_defs"][pref_m]

    h_o = {**h_o_defs, "target_values": []}

    for bs_id in prevars["query"]["biosample_id"]["$in"]:
        for v in data_db["variants"].find({"biosample_id": bs_id}):
            h_o["target_values"].append(v["_id"])

    h_o.update(
        {
            "id": str(uuid4()),
            "source_db": prevars["ds_id"],
            "target_count": len(h_o["target_values"]),
            "original_queries": prevars.get("original_queries", None)
        }
    )

    return h_o


################################################################################

def _prefetch_add_individuals(prevars, prefetch):
    prevars["pref_m"] = "biosamples.individual_id->individuals.id"
    prevars["query"] = {"_id": {"$in": prefetch["biosamples._id"]["target_values"]}}
    prefetch.update({"individuals.id": _prefetch_data(prevars)})

    prevars["pref_m"] = "individuals._id"
    prevars["query"] = {"id": {"$in": prefetch["individuals.id"]["target_values"]}}
    prefetch.update({prevars["pref_m"]: _prefetch_data(prevars)})

    return prefetch


################################################################################
