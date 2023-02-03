from pymongo import MongoClient
from bson.son import SON
from uuid import uuid4
# import logging
import datetime
import sys

from cgi_parsing import cgi_debug_message, test_truthy

################################################################################

def mongo_result_list(db_name, coll_name, query, fields):

    results = [ ]
    error = False

    mongo_client = MongoClient( )

    try:
        results = list( mongo_client[ db_name ][ coll_name ].find( query, fields ) )
    except Exception as e:
        error = e

    mongo_client.close( )
 
    return results, error

################################################################################

def process_empty_request(ds_id, collname, byc, ret_no=10):

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    data_coll = mongo_client[ ds_id ][ collname ]

    c = data_coll.estimated_document_count()
    r = list( data_coll.aggregate([{"$sample": {"size":ret_no}}]) )

    return r, c

################################################################################

def execute_bycon_queries(ds_id, byc):

    max_bs_number_for_v_in_query = 2500

    # last_time = datetime.datetime.now()
    # logging.info("\t start query: {}".format(last_time))

    """podmd
    
    Pre-configured queries are performed in an aggregation pipeline against
    the standard "Progenetix"-type MongoDB collections.
        
    podmd"""

    h_o_defs = byc[ "handover_definitions" ]["h->o_methods"]

    exe_queries = { }
    if not "dataset_results" in byc.keys():
        byc.update({"dataset_results":{}})

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    data_collnames = data_db.list_collection_names()

    ho_client = MongoClient()
    ho_db = ho_client[ byc["config"]["info_db"] ]
    ho_collname = byc["config"][ "handover_coll" ]
    ho_coll = ho_db[ ho_collname ]

    if test_truthy( byc["form_data"].get("annotated_only", False) ):
        if "variants" in byc["queries"]:
            byc["queries"].update({"variants": { "$and": [ byc["queries"]["variants"], {"info.annotation_derived":True} ] } } )
        else:
            byc["queries"].update( {"variants": {"info.annotation_derived":True} } )

    # print(byc[ "queries" ])
    # exit()

    for collname in byc[ "queries" ].keys():
        if collname in byc[ "config" ][ "queried_collections" ]:
            exe_queries[ collname ] = byc[ "queries" ][ collname ]

    byc.update({"queries_at_execution": exe_queries})

    if byc["original_queries"] is None:
        byc.update({"original_queries": exe_queries})

    # print(byc["original_queries"])

    # collection of results
    prefetch = { }
    prevars = { 
        "ds_id": ds_id,
        "data_db": data_db,
        "h_o_defs": h_o_defs,
        "original_queries": byc["original_queries"],
        "pref_m": "", "query": { }
    }

    ############################################################################

    cgi_debug_message(byc, "queries at execution", exe_queries)

    ############################################################################

    if "variant_annotations" in exe_queries:

        prevars["pref_m"] = "variant_annotations._id"
        prevars["query"] = exe_queries[ "variant_annotations" ]
        prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )
        byc["dataset_results"].update( { ds_id: prefetch } )

        return byc

    ############################################################################

    """podmd
    
    All queries are aggregated towards biosamples.
        
    podmd"""

    if "biosamples" in exe_queries:

        prevars["pref_m"] = "biosamples.id"
        prevars["query"] = exe_queries[ "biosamples" ]
        prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

    if "individuals" in exe_queries:

        prevars["pref_m"] = "individuals.id"
        prevars["query"] = exe_queries[ "individuals" ]
        prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

        prevars["pref_m"] = "biosamples.id"
        prevars["query"] = { "individual_id": { '$in': prefetch["individuals.id"]["target_values"] }  }
        biosids_from_indq =  _prefetch_data(prevars)

        if "biosamples.id" in prefetch:
            bsids = list( set( biosids_from_indq["target_values"] ) & set( prefetch["biosamples.id"]["target_values"] ) )
            prefetch[ "biosamples.id" ].update( { "target_values": bsids, "target_count": len(bsids) } )
        else:
            prefetch["biosamples.id"] = biosids_from_indq

    if "callsets" in exe_queries:

        # since callsets contain biosample_id no double calling is required
        prevars["pref_m"] = "callsets.biosample_id->biosamples.id"
        prevars["query"] = exe_queries[ "callsets" ]
        prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

        if "biosamples.id" in prefetch:
            bsids = list( set( prefetch["callsets.biosample_id->biosamples.id"]["target_values"] ) & set( prefetch["biosamples.id"]["target_values"] ) )
            prefetch[ "biosamples.id" ].update( { "target_values": bsids, "target_count": len(bsids) } )
        else:
            prefetch["biosamples.id"] = prefetch["callsets.biosample_id->biosamples.id"]

    if "variants" in exe_queries:

        if exe_queries["variants"]:

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
            prevars["query"] = exe_queries[ "variants" ]
            prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

            if "biosamples.id" in prefetch:
                bsids = list( set( prefetch["biosamples.id"]["target_values"] ) & set( prefetch["variants.biosample_id->biosamples.id"]["target_values"] ) )
                prefetch[ "biosamples.id" ].update( { "target_values": bsids, "target_count": len(bsids) } )
                exe_queries[ "variants" ] = { "$and": [ exe_queries[ "variants" ], { "biosample_id": { "$in": bsids } } ] }
            else:
                prefetch[ "biosamples.id" ] = prefetch["variants.biosample_id->biosamples.id"]

            prevars["pref_m"] = "variants._id"
            prevars["query"] = exe_queries[ "variants" ]
            prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

            prevars["pref_m"] = "variants.variant_internal_id"
            prevars["query"] = { "_id": { "$in": prefetch[ "variants._id" ]["target_values"] } }
            prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

            # print(prefetch["variants.variant_internal_id"]["target_values"])


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

    if not "biosamples.id" in prefetch:

        prefetch.update({"biosamples.id": { **prevars["h_o_defs"]["biosamples.id"]}})
        prefetch["biosamples.id"].update({
            "id": str(uuid4()),
            "source_db": ds_id,
            "target_values": [],
            "target_count": 0
            })

        byc["dataset_results"].update( { ds_id: prefetch } )
        return byc

    prevars["pref_m"] = "callsets._id"
    prevars["query"] = { "biosample_id": { "$in": prefetch[ "biosamples.id" ]["target_values"] } }
    prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

    prevars["pref_m"] = "biosamples._id"
    prevars["query"] = { "id": { "$in": prefetch[ "biosamples.id" ]["target_values"] } }
    prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

    # TODO: have this checked... somewhere else based on the response_entity_id
    if "response_entity_id" in byc:
        if "individual" in byc["response_entity_id"] or "phenopacket" in byc["response_entity_id"]:
            _prefetch_add_individuals(prevars, prefetch)
        elif "genomicVariant" in byc["response_entity_id"] and not "variants._id"  in prefetch:
            _prefetch_add_all_sample_variants(prevars, prefetch)

    if "variant_annotations" in data_collnames:
        if "variants._id" in prefetch:
            _prefetch_add_variant_annotations(prevars, prefetch)
    
    ############################################################################

    data_client.close( )
    ho_client.close( )

    byc["dataset_results"].update( { ds_id: prefetch } )

    return byc

################################################################################

def _prefetch_data(prevars):

    """podmd
    The prefetch pref_m queries the specified collection `source_collection` of
    the `data_db` with the provided query, and stores the distinct values of the
    `source_key` as `target_values`.

    The results may reference across collections. A typica example here would be
    to retrieve `biosaample_id` values from the `variants` collection to point
    to `id` values in the `biosamples` collection.

    These "handover" objects can then be stored and used to retrieve values of
    previous queries for procedural use or second-pass data retrieval.

    podmd"""

    pref_m = prevars["pref_m"]
    data_db = prevars["data_db"]
    h_o_defs = prevars["h_o_defs"][pref_m]

    dist = data_db[ h_o_defs["source_collection"] ].distinct( h_o_defs["source_key"], prevars["query"] )

    h_o = { **h_o_defs }
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

def _prefetch_vars_from_biosample_loop( prevars ):

    # TODO: This still allows unlimited variants, e.g. all from thousands
    # of samples and will let the server time out if too many...
    # A new paradigm is needed which includes the pagination at this step.

    pref_m = prevars["pref_m"]
    data_db = prevars["data_db"]
    h_o_defs = prevars["h_o_defs"][pref_m]

    h_o = { **h_o_defs }
    h_o["target_values"] = [ ]

    for bs_id in prevars["query"]["biosample_id"]["$in"]:
        for v in data_db[ "variants" ].find( { "biosample_id": bs_id} ):
            h_o["target_values"].append( v["_id"])

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
    prevars["query"] = { "_id": { "$in": prefetch[ "biosamples._id" ]["target_values"] } }
    prefetch.update( { "individuals.id": _prefetch_data(prevars) } )

    prevars["pref_m"] = "individuals._id"
    prevars["query"] = { "id": { "$in": prefetch[ "individuals.id" ]["target_values"] } }
    prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

    return prefetch

################################################################################

def _prefetch_add_all_sample_variants(prevars, prefetch):

    prevars["pref_m"] = "variants._id"
    prevars["query"] = { "biosample_id": { "$in": prefetch[ "biosamples.id" ]["target_values"] } }
    prefetch.update( { prevars["pref_m"]: _prefetch_vars_from_biosample_loop( prevars ) } )
    # print("Storage size for {} entries in {}: {}".format(prefetch[prevars["pref_m"]]["target_count"], prevars["pref_m"], sys.getsizeof(prefetch[prevars["pref_m"]]["target_values"]) / 1000000))

    return prefetch

################################################################################

def _prefetch_add_variant_annotations(prevars, prefetch):

    prevars["pref_m"] = "variants.variantannotation_id->variant_annotations.id"
    prevars["query"] = { "_id": { "$in": prefetch[ "variants._id" ]["target_values"] } }
    prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

    prevars["pref_m"] = "variant_annotations._id"
    prevars["query"] = { "id": { "$in": prefetch[ "variants.variantannotation_id->variant_annotations.id" ]["target_values"] } }
    prefetch.update( { prevars["pref_m"]: _prefetch_data(prevars) } )

    return prefetch


