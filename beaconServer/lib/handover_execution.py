from pymongo import MongoClient

################################################################################

def retrieve_handover( accessid, byc ):

    mongo_client = MongoClient()
    ho_d = byc["config"]["info_db"]
    ho_c = byc["config"][ "handover_coll" ]
    ho_coll = mongo_client[ ho_d ][ ho_c ]

    h_o = { }
    error = False

    try:
        h_o =  ho_coll.find_one( { "id": accessid } )
    except:
        pass

    mongo_client.close( )

    return h_o, error

###############################################################################

def handover_return_data( h_o, byc, error=False ):

    # TODO: alternative as loop over data, if target_count very high

    mongo_client = MongoClient()
    data = [ ]

    if not error:
        data_coll = mongo_client[ h_o["source_db"] ][ h_o[ "target_collection" ] ]
        if h_o["target_count"] > 1000000:   # for the MongoDB 16MB doc limit
            for t in data_coll.find( {} ):
                if t[ h_o["target_key"] ] in h_o["target_values"]:
                    data.append(t)
        else:
            query = { h_o["target_key"]: { '$in': h_o["target_values"] } }
            for c in data_coll.find( query ):  # , {'_id': False }
                data.append(c)
    else:
        pass
    # TODO: error messaging

    mongo_client.close( )

    return data, error
