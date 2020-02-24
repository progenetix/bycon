from pymongo import MongoClient

########################################################################################################################
########################################################################################################################
########################################################################################################################


def return_callsets_stats(**kwargs):

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ kwargs[ "config" ][ "data_pars" ][ "dataset_id" ] ]
    mongo_coll = mongo_db[ 'callsets' ]

    cs_stats = { }
    cs_stats["dup_fs"] = []
    cs_stats["del_fs"] = []
    cs_stats["cnv_fs"] = []

    for cs in mongo_coll.find({"_id": {"$in": kwargs["callsets::_id"] }}) :
        if "cnvstatistics" in cs["info"]:
            if "dupfraction" in cs["info"]["cnvstatistics"] and "delfraction" in cs["info"]["cnvstatistics"]:
                cs_stats["dup_fs"].append(cs["info"]["cnvstatistics"]["dupfraction"])
                cs_stats["del_fs"].append(cs["info"]["cnvstatistics"]["delfraction"])
                cs_stats["cnv_fs"].append(cs["info"]["cnvstatistics"]["cnvfraction"])

    mongo_client.close()

    return cs_stats

########################################################################################################################

