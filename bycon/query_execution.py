from pymongo import MongoClient
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

    query_types = byc[ "queries" ].keys()
    for collname in byc[ "queries" ]:
        if collname in byc[ "config" ][ "collections" ]:
            exe_queries[ collname ] = byc[ "queries" ][ collname ]

    # collection of results

    prefetch = { }
    prevars = { "ds_id": ds_id, "mdb": data_db, "h_o_defs": h_o_defs, "method": "", "query": { } }

    # TODO: to be implemented ...
    if ho_collname in exe_queries:
        
        handover = ho_coll.find_one( exe_queries[ q_coll_name ] )

    if "individuals" in exe_queries:

        prevars["method"] = "is.id"
        prevars["query"] = exe_queries[ "individuals" ]
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        prevars["method"] = "bs.isid->bs.id"
        prevars["query"] = { "individual_id": { '$in': prefetch["is.id"]["target_values"] }  }
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        # TODO: finishing this ... 

    if "biosamples" in exe_queries:

        prevars["method"] = "bs.id"
        prevars["query"] = exe_queries[ "biosamples" ]
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        # TODO: Introduce a way to pre-define which queries have to be
        # run. E.g. when only retrieving biosample data, it makes no
        # sense to also run a callsets query.

        prevars["method"] = "cs.bsid->cs.id"
        prevars["query"] = { "biosample_id": { '$in': prefetch["bs.id"]["target_values"] }  }
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

    if "callsets" in exe_queries:

        prevars["method"] = "cs.id"
        prevars["query"] = exe_queries[ "callsets" ]
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        if "cs.bsid->cs.id" in prefetch:
            csids = list( set( prefetch["cs.bsid->cs.id"]["target_values"] ) & set( prefetch["cs.id"]["target_values"] ) )
            prefetch[ "cs.id" ].update( { "target_values": csids, "target_count": len(csids) } )

    # if no callsets query but existing output from biosample query -> rename
    elif "cs.bsid->cs.id" in prefetch:

        prefetch[ "cs.id" ] = prefetch[ "cs.bsid->cs.id" ]

    if "variants" in exe_queries:

        """podmd
        ### `variants` Query and Aggregation

        1. If a `variants` query exists (i.e. has been defined in `exe_queries`), in a first pass
        all `callset_id` values are retrieved.
        2. If already a `"cs.id"` result exists (e.g. from a biosample query), the lists
        of callset `id` values from the different queries are intersected. Otherwise, the callsets
        from the variants query are the final ones.
        3. Since so far not all matching variants have been retrieved (only the callsets which
        contain them), they are now fetched using the original query or a combination of the
        original query and the matching callsets from the intersect.
        podmd"""

        prevars["method"] = "vs.csid->cs.id"
        prevars["query"] = exe_queries[ "variants" ]
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )
          
        if "cs.id" in prefetch:
            csids = list( set( prefetch["cs.id"]["target_values"] ) & set( prefetch["vs.csid->cs.id"]["target_values"] ) )
            prefetch[ "cs.id" ].update( { "target_values": csids, "target_count": len(csids) } )
            exe_queries[ "variants" ] = { "$and": [ exe_queries[ "variants" ], { "callset_id": { "$in": csids } } ] }
        else:
            prefetch[ "cs.id" ] = prefetch["vs.csid->cs.id"]
            prefetch[ "cs.id" ].update( { "source_collection": h_o_defs["cs.id"]["source_collection"], "source_key": h_o_defs["cs.id"]["source_key"] } )

        prevars["method"] = "vs._id"
        prevars["query"] = exe_queries[ "variants" ]
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

        prevars["method"] = "vs.digest"
        prevars["query"] = { "_id": { "$in": prefetch[ "vs._id" ]["target_values"] } }
        prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

    """podmd
    ### Result Aggregation

    The above queries have provided `cs.id` values which now are used to retrieve the
    matching final biosample `id` and `_id` values.

    TODO: Benchmark if the `_id` retrieval & storage speeds up biosample and callset recovery
    in handover scenarios or if `id` is fine.
    podmd"""

    prevars["method"] = "cs._id"
    prevars["query"] = { "id": { "$in": prefetch[ "cs.id" ]["target_values"] } }
    prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

    prevars["method"] = "cs.bsid->bs.id"
    prevars["query"] = { "_id": { "$in": prefetch[ "cs._id" ]["target_values"] } }
    prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

    prefetch[ "bs.id" ] = prefetch["cs.bsid->bs.id"]
    prefetch[ "bs.id" ].update( { "source_collection": h_o_defs["bs.id"]["source_collection"], "source_key": h_o_defs["bs.id"]["source_key"] } )

    prevars["method"] = "bs._id"
    prevars["query"] = { "id": { "$in": prefetch[ "bs.id" ]["target_values"] } }
    prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )

    """podmd
    If no variant query was performed _but_ the response asks for variants => all
    callset variants will be returned.

    podmd"""

    # TODO: This will need to be refined; queries can potentially lead to huge responses here...
    if byc["response_type"] == "return_variants":
        if not "vs._id" in prefetch.keys():
            prevars["method"] = "vs._id"
            prevars["query"] = { "callset_id": { "$in": prefetch[ "cs.id" ]["target_values"] } }
            prefetch.update( { prevars["method"]: _prefetch_data( **prevars ) } )
    
    data_client.close( )
    ho_client.close( )

    return prefetch

################################################################################

def _prefetch_data( **prevars ):

    method = prevars["method"]
    data_db = prevars["mdb"]
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

