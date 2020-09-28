from pymongo import MongoClient
from bson.son import SON
from uuid import uuid4
import logging
import datetime

################################################################################

def execute_bycon_queries(ds_id, **byc):

    # last_time = datetime.datetime.now()
    # logging.info("\t start query: {}".format(last_time))

    """podmd
    
    Pre-configured queries are performed in an aggregation pipeline against
    the standard "Progenetix"-type MongoDB collections.
        
    podmd"""

    h_o_defs = byc[ "h->o" ]["h->o_methods"]

    exe_queries = { }
    # last_time = byc[ "last_time" ]

    data_client = MongoClient( )
    data_db = data_client[ ds_id ]
    ho_client = MongoClient()
    ho_db = ho_client[ byc["config"]["info_db"] ]
    ho_collname = byc["config"][ "handover_coll" ]
    ho_coll = ho_db[ ho_collname ]

    for collname in byc[ "queries" ].keys():
        if collname in byc[ "config" ][ "collections" ]:
            exe_queries[ collname ] = byc[ "queries" ][ collname ]

    # collection of results

    prefetch = { }
    prevars = { "ds_id": ds_id, "data_db": data_db, "h_o_defs": h_o_defs, "method": "", "query": { } }

    """podmd
    
    All queries are aggregated towards biosamples.
        
    podmd"""

    if "biosamples" in exe_queries:

        prevars["method"] = "bs.id"
        prevars["query"] = exe_queries[ "biosamples" ]
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

    if "individuals" in exe_queries:

        prevars["method"] = "is.id"
        prevars["query"] = exe_queries[ "individuals" ]
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        prevars["method"] = "bs.isid->bs.id"
        prevars["query"] = { "individual_id": { '$in': prefetch["is.id"]["target_values"] }  }
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        if "bs.id" in prefetch:
            bsids = list( set( prefetch["bs.isid->bs.id"]["target_values"] ) & set( prefetch["bs.id"]["target_values"] ) )
            prefetch[ "bs.id" ].update( { "target_values": bsids, "target_count": len(bsids) } )
        else:
            prefetch["bs.id"] = prefetch["bs.isid->bs.id"]

    if "callsets" in exe_queries:

        # since callsets contain biosample_id no double calling is required
        prevars["method"] = "cs.bsid->bs.id"
        prevars["query"] = exe_queries[ "callsets" ]
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        if "bs.id" in prefetch:
            bsids = list( set( prefetch["cs.bsid->bs.id"]["target_values"] ) & set( prefetch["bs.id"]["target_values"] ) )
            prefetch[ "bs.id" ].update( { "target_values": bsids, "target_count": len(bsids) } )
        else:
            prefetch["bs.id"] = prefetch["cs.bsid->bs.id"]

    if "variants" in exe_queries:

        if exe_queries["variants"]:

            """podmd
            ### `variants` Query and Aggregation

            1. If a `variants` query exists (i.e. has been defined in `exe_queries`), in a first pass
            all `biosample_id` values are retrieved.
            2. If already a `"bs.id"` result exists (e.g. from a biosample query), the lists
            of callset `id` values from the different queries are intersected. Otherwise, the callsets
            from the variants query are the final ones.
            3. Since so far not all matching variants have been retrieved (only the biosamples which
            contain them), they are now fetched using the original query or a combination of the
            original query and the matching biosamples from the intersect.
            podmd"""

            prevars["method"] = "vs.bsid->bs.id"
            prevars["query"] = exe_queries[ "variants" ]
            prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )
              
            if "bs.id" in prefetch:
                bsids = list( set( prefetch["bs.id"]["target_values"] ) & set( prefetch["vs.bsid->bs.id"]["target_values"] ) )
                prefetch[ "bs.id" ].update( { "target_values": bsids, "target_count": len(bsids) } )
                exe_queries[ "variants" ] = { "$and": [ exe_queries[ "variants" ], { "biosample_id": { "$in": bsids } } ] }
            else:
                prefetch[ "bs.id" ] = prefetch["vs.bsid->bs.id"]

            prevars["method"] = "vs._id"
            prevars["query"] = exe_queries[ "variants" ]
            prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

            prevars["method"] = "vs.digest"
            prevars["query"] = { "_id": { "$in": prefetch[ "vs._id" ]["target_values"] } }
            prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )



    """podmd
    ### Result Aggregation

    The above queries have provided `bs.id` values which now are used to retrieve the
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

    prevars["method"] = "cs._id"
    prevars["query"] = { "biosample_id": { "$in": prefetch[ "bs.id" ]["target_values"] } }
    prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

    prevars["method"] = "bs._id"
    prevars["query"] = { "id": { "$in": prefetch[ "bs.id" ]["target_values"] } }
    prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

    if "response_type" in byc:

        if byc["response_type"] == "return_variants":
            if not "vs._id" in prefetch.keys():
                prevars["method"] = "vs._id"
                prevars["query"] = { "biosample_id": { "$in": prefetch[ "bs.id" ]["target_values"] } }
                prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        if "individuals" in byc["response_type"] or "phenopackets" in byc["response_type"]:
            prevars["method"] = "bs.isid->is.id"
            prevars["query"] = { "_id": { "$in": prefetch[ "bs._id" ]["target_values"] } }
            prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

            prevars["method"] = "is._id"
            prevars["query"] = { "id": { "$in": prefetch[ "bs.isid->is.id" ]["target_values"] } }
            prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )
    
    ############################################################################

    data_client.close( )
    ho_client.close( )

    return prefetch

################################################################################

def _prefetch_data( **prevars ):

    """podmd
    The prefetch method queries the specified collection `source_collection` of
    the `data_db` with the provided query, and stores the distinct values of the
    `source_key` as `target_values`.

    The results may reference across collections. A typica example here would be
    to retrieve `biosaample_id` values from the `variants` collection to point
    to `id` values in the `biosamples` collection.

    These "handover" objects can then be stored and used to retrieve values of
    previous queries for procedural use or second-pass data retrieval.

    podmd"""

    method = prevars["method"]
    data_db = prevars["data_db"]
    h_o_defs = prevars["h_o_defs"][method]

    dist = data_db[ h_o_defs["source_collection"] ].distinct( h_o_defs["source_key"], prevars["query"] )

    h_o = { **h_o_defs }
    h_o.update(
        {
            "id": str(uuid4()),
            "source_db": prevars["ds_id"],
            "target_values": dist,
            "target_count": len(dist)
        }
    )

    return(h_o)

################################################################################

