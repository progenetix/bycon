from pymongo import MongoClient
import logging
import datetime

def execute_bycon_queries(**kwargs):

    # last_time = datetime.datetime.now()
    # logging.info("\t start query: {}".format(last_time))

    """podmd
    
    Pre-configured queries are performed in an aggregation pipeline against
    the standard "Progenetix"-type MongoDB collections.
        
    podmd"""

    query_results = { "info": { } }
    for collname in kwargs[ "config" ][ "collections" ]:
        query_results[ collname+"::id" ] = [ ]
        query_results[ collname+"::_id" ] = [ ]
    query_results[ "variants::digest" ] = [ ]

    exe_queries = { }
    dataset_id = kwargs[ "dataset_id" ]
    last_time = kwargs[ "last_time" ]

    mongo_client = MongoClient( )

    query_types = kwargs[ "queries" ].keys()
    for collname in kwargs[ "queries" ]:
        if collname in kwargs[ "config" ][ "collections" ]:
            exe_queries[ collname ] = kwargs[ "queries" ][ collname ]

    q_coll_name = "querybuffer"
    if q_coll_name in exe_queries:
        mongo_db = mongo_client[ "progenetix" ]
        mongo_coll = mongo_db[ q_coll_name ]
        
        handover = mongo_coll.find_one( exe_queries[ q_coll_name ] )

    mongo_db = mongo_client[ dataset_id ]

    if "biosamples" in exe_queries:

        query_results[ "biosamples::id" ] = mongo_db[ "biosamples" ].distinct( "id", exe_queries[ "biosamples" ] )
                
        # TODO: Introduce a way to pre-define which queries have to be
        # run. E.g. when only retrieving biosample data, it makes no
        # sense to also run a callsets query.

        cs_from_bs = mongo_db[ "callsets" ].distinct( "id", { "biosample_id": {"$in": query_results["biosamples::id"] } } )

    logging.info("\t biosamples: {}".format(datetime.datetime.now()-last_time))
    last_time = datetime.datetime.now()

    if "callsets" in exe_queries:
        query_results[ "callsets::id" ] = mongo_db[ "callsets" ].distinct( "id", exe_queries[ "callsets" ] )
        if "biosamples" in exe_queries:
            query_results[ "callsets::id" ] = set(cs_from_bs & query_results[ "callsets::id" ])
    elif "biosamples" in exe_queries:
        query_results[ "callsets::id" ] = cs_from_bs

    logging.info("\t callsets: {}".format(datetime.datetime.now()-last_time))
    logging.info("\t\t callsets count: {}".format(len(query_results[ "callsets::id" ])))
    last_time = datetime.datetime.now()

    if "variants" in exe_queries:

        """podmd
        ### `variants` Query and Aggregation

        1. If a `variants` query exists (i.e. has been defined in `exe_queries`), in a first pass
        all `callset_id` values are retrieved.
        2. If already a `"callsets::id"` result exists (e.g. from a biosample query), the lists
        of callset `id` values from the different queries are intersected. Otherwise, the callsets
        from the variants query are the final ones.
        3. Since so far not all matching variants have been retrieved (only the callsets which
        contain them), they are now fetched using the original query or a combination of the
        original query and the matching callsets from the intersect.
        podmd"""
           
        mongo_vars = mongo_db[ 'variants' ]
        cs_from_vars = mongo_vars.distinct( "callset_id", exe_queries[ "variants" ] )
        # print(exe_queries[ "variants" ])

        logging.info("\t\t cs_from_vars: {}".format(datetime.datetime.now()-last_time))
        last_time = datetime.datetime.now()
        # print(len(cs_from_vars))
        # print(len(query_results[ "callsets::id" ]))

        if "callsets::id" in query_results:
            query_results[ "callsets::id" ] = list(set(cs_from_vars) & set(query_results[ "callsets::id" ]))
            exe_queries[ "variants" ] = { "$and": [ exe_queries[ "variants" ], { "callset_id": {"$in": query_results[ "callsets::id" ] } } ] }
        else:
            query_results[ "callsets::id" ] = cs_from_vars

        # print(len(query_results[ "callsets::id" ]))

        # print("requery vars")
        query_results[ "variants::_id" ] = mongo_vars.distinct( "_id", exe_queries[ "variants" ] )
        logging.info("\t\t variants_id: {}".format(datetime.datetime.now()-last_time))
        logging.info("\t\t variants count: {}".format(len(query_results[ "variants::_id" ])))
        last_time = datetime.datetime.now()

        # print("requery vars for digests")
        query_results[ "variants::digest" ] = mongo_vars.distinct( "digest", { "_id": {"$in": query_results[ "variants::_id" ] } } )

        logging.info("\t\t variants_digest: {}".format(datetime.datetime.now()-last_time))
        logging.info("\t\t digests count: {}".format(len(query_results[ "variants::digest" ])))

        last_time = datetime.datetime.now()

    logging.info("\t variants: {}".format(datetime.datetime.now()-last_time))
    last_time = datetime.datetime.now()

    """podmd
    ### Result Aggregation

    The above queries have provided `callsets::id` values which now are used to retrieve the
    matching final biosample `id` and `_id` values.

    TODO: Benchmark if the `_id` retrieval & storage speeds up biosample and callset recovery
    in handover scenarios or if `id` is fine.
    podmd"""

    query_results[ "callsets::_id" ] = mongo_db[ 'callsets' ].distinct( "_id", {
            "id": { "$in": query_results[ "callsets::id" ] } } )        
    logging.info("\t callsets::_id: {}".format(datetime.datetime.now()-last_time))
    last_time = datetime.datetime.now()

    query_results[ "biosamples::id" ] = mongo_db[ 'callsets' ].distinct( "biosample_id", {
        "_id": { "$in": query_results[ "callsets::_id" ] } } )         
    logging.info("\t biosamples::id: {}".format(datetime.datetime.now()-last_time))
    last_time = datetime.datetime.now()

    query_results[ "biosamples::_id" ] = mongo_db[ 'biosamples' ].distinct( "_id", { "id": { "$in": query_results[ "biosamples::id" ] } } )
    logging.info("\t biosamples::_id: {}".format(datetime.datetime.now()-last_time))
    last_time = datetime.datetime.now()

    query_results[ "counts" ] = { }
    for scope in [ "callsets", "biosamples" ]:
        query_results[ "counts" ][ scope ] = len( query_results[ scope+"::_id" ] )
        query_results[ "counts" ][ scope+"_all" ] =  mongo_db[ scope ].estimated_document_count()
        logging.info("\t counts for all "+scope+": {}".format(datetime.datetime.now()-last_time))
        last_time = datetime.datetime.now()

    query_results[ "counts" ][ "variants" ] =  len(query_results[ "variants::digest" ])
    query_results[ "counts" ][ "variants_all" ] =  mongo_db[ "variants" ].estimated_document_count()
    logging.info("\t variant counts: {}".format(datetime.datetime.now()-last_time))
    last_time = datetime.datetime.now()

    mongo_client.close( )   

    return query_results
