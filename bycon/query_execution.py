from pymongo import MongoClient

def execute_bycon_queries(**kwargs):

    query_results = { }
    exe_queries = { }
    dataset_id = kwargs[ "config" ][ "data_pars" ][ "dataset_id" ]

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ dataset_id ]

    for collname in kwargs[ "config" ][ "dataset_ids" ]:
        if collname in kwargs[ "queries" ]:
            exe_queries[ collname ] = kwargs[ "queries" ][ collname ]

    # biosamples first, since besides variants the obvious query target
    mongo_coll = mongo_db[ 'biosamples' ]
    if "biosamples" in exe_queries:
        query_results["biosample::_id"] = mongo_coll.distinct( "_id", exe_queries[ "biosamples" ] )
        query_results["biosample::id"] = mongo_coll.distinct( "id", {"_id": {"$in": query_results["biosample::_id"] } })
        print( str( len( query_results[ "biosample::_id" ] ) ) + " biosamples were found from biosamples query" )
        if "callsets" in exe_queries:
            exe_queries[ "callsets" ] = { "$and": [ exe_queries[ "callsets" ], {"biosample_id": {"$in": query_results["biosample::id"] } } ] }
        else:
            exe_queries[ "callsets" ] = {"biosample_id": {"$in": query_results["biosample::id"] } }

    mongo_coll = mongo_db[ 'callsets' ]
    if "callsets" in exe_queries:
        query_results["callsets::_id"] = mongo_coll.distinct( "_id", exe_queries[ "callsets" ] )
        query_results["callsets::id"] = mongo_coll.distinct( "id", {"_id": {"$in": query_results["callsets::_id"] } })
        query_results["biosamples::id"] = mongo_coll.distinct( "biosample_id", {"_id": {"$in": query_results["callsets::_id"] } })
        print( str( len( query_results[ "callsets::_id" ] ) ) + " callsets were found from callsets query" )
        print( str( len( query_results[ "biosamples::id" ] ) ) + " biosamples were found from callsets query" )
        if "variants" in exe_queries:
            print(exe_queries["variants"])
            print("¡¡¡variants query exists!!!")
            exe_queries[ "variants" ] = { "$and": [ exe_queries[ "variants" ], {"callset_id": {"$in": query_results["callsets::id"] } } ] }
            mongo_coll = mongo_db[ 'variants' ]
            query_results["variants::_id"] = mongo_coll.distinct( "_id", exe_queries[ "variants" ] )
            query_results[ "callsets::id" ] = mongo_coll.distinct( "callset_id", exe_queries[ "variants" ] )
            mongo_coll = mongo_db[ 'callsets' ]
            query_results[ "callsets::_id" ] = mongo_coll.distinct( "_id", {
                "id": { "$in": query_results[ "callsets::id" ] } } )
            print( str( len( query_results[ "callsets::_id" ] ) ) + " callsets were found after variants query" )

    # mongo_coll = mongo_db[ 'callsets' ]
    # query_results[ "biosamples::id" ] = mongo_coll.distinct( "biosample_id", { "_id": { "$in": query_results[ "callsets::_id" ] } } )
    # print(str(len(query_results["biosamples::id"]))+" biosample_id values were found in aggregated callsets")
    # mongo_coll = mongo_db[ 'biosamples' ]
    # query_results["biosamples::_id"] = mongo_coll.distinct( "_id", { "id": { "$in": query_results[ "biosamples::id" ] } } )

    if "variants::_id" in query_results:
        print(str(len(query_results["variants::_id"]))+" variants were found")

    print(str(len(query_results["biosamples::id"]))+" biosamples were found")

    mongo_client.close( )

    return query_results