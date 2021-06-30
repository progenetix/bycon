from pymongo import MongoClient

################################################################################

def handover_retrieve_from_query_results(ds_id, byc):

    h_o = { }
    e = "No data fround for {} response type!".format(byc["response_type"])

    for r_t, r_d in byc["beacon_mappings"]["response_types"].items():
        if r_d["id"] == byc["response_type"]:
            if r_d["h->o_access_key"] in byc["dataset_results"][ds_id]:
                return byc["dataset_results"][ds_id][ r_d["h->o_access_key"] ], False

    return h_o, e

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

def handover_return_data( h_o, error=False ):

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
