from pymongo import MongoClient

def execute_bycon_queries(**kwargs):

    """podmd
    
    Pre-configured queries are performed in an aggregation pipeline against
    the standard "Progenetix"-type MongoDB collections.
        
    podmd"""

    query_results = { }
    exe_queries = { }
    dataset_id = kwargs[ "config" ][ "data_pars" ][ "dataset_id" ]

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

    q_coll_name = "biosamples"  

    if q_coll_name in exe_queries:

        mongo_coll = mongo_db[ q_coll_name ]
        query_results[ "biosamples::_id"] = mongo_coll.distinct( "_id", exe_queries[ q_coll_name ] )
        query_results["biosamples::id"] = mongo_coll.distinct( "id", {"_id": {"$in": query_results["biosamples::_id"] } })
        
        """podmd
        If there is a predefined callsets query, it will be combined
        with a query for the callsets matching the found biosamples.
        
        Otherwise only the biosamples match will be queried for callsets.
        podmd"""
        
        # TODO: Introduce a way to pre-define which queries have to be
        # run. E.g. when only retrieving biosample data, it makes no
        # sense to also run a callsets query.

        if "callsets" in exe_queries:
            exe_queries[ "callsets" ] = { "$and": [ exe_queries[ "callsets" ], {"biosample_id": {"$in": query_results["biosamples::id"] } } ] }
        else:
            exe_queries[ "callsets" ] = {"biosample_id": {"$in": query_results["biosamples::id"] } }

    q_coll_name = "callsets"

    if q_coll_name in exe_queries:

        mongo_coll = mongo_db[ q_coll_name ]
        query_results["callsets::_id"] = mongo_coll.distinct( "_id", exe_queries[ q_coll_name ] )
        query_results["callsets::id"] = mongo_coll.distinct( "id", {"_id": {"$in": query_results["callsets::_id"] } })

        q_coll_name = "variants"

        if q_coll_name in exe_queries:
            
            mongo_coll = mongo_db[ q_coll_name ]

            exe_queries[ q_coll_name ] = { "$and": [ exe_queries[ q_coll_name ], {"callset_id": {"$in": query_results["callsets::id"] } } ] }

            query_results["variants::_id"] = mongo_coll.distinct( "_id", exe_queries[ "variants" ] )
            query_results[ "callsets::id" ] = mongo_coll.distinct( "callset_id", exe_queries[ "variants" ] )

            mongo_coll = mongo_db[ 'callsets' ]
            query_results[ "callsets::_id" ] = mongo_coll.distinct( "_id", {
                "id": { "$in": query_results[ "callsets::id" ] } } )
            query_results[ "biosamples::id" ] = mongo_coll.distinct( "biosample_id", {
                "_id": { "$in": query_results[ "callsets::_id" ] } } )
            
        mongo_coll = mongo_db[ 'biosamples' ]            
        query_results["biosamples::_id"] = mongo_coll.distinct( "_id", { "id": { "$in": query_results[ "biosamples::id" ] } } )

    mongo_client.close( )   

    return query_results
