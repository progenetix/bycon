from pymongo import MongoClient
from bycon import BYC, DB_MONGOHOST, HOUSEKEEPING_DB, HOUSEKEEPING_INFO_COLL, print_json_response
from byconServiceLibs import ByconServiceResponse

def dbstats():
    """
    This service endpoint provides statistic information about the resource's
    datasets.

    #### Examples
    
    * <https://progenetix.org/services/dbstats/>
    * <https://progenetix.org/services/dbstats/examplez>
    """
    stats_client = MongoClient(host=DB_MONGOHOST)
    stats_coll = stats_client[HOUSEKEEPING_DB][HOUSEKEEPING_INFO_COLL]
    results = []
    stats = stats_coll.find({}, {"_id": 0 }).sort("date", -1).limit(1)
    stat = list(stats)[0]
    for ds_id, ds_vs in stat["datasets"].items():
        if len(BYC["BYC_DATASET_IDS"]) > 0:
            if not ds_id in BYC["BYC_DATASET_IDS"]:
                continue
        results.append( {"dataset_id": ds_id, "counts":ds_vs["counts"]} )

    ByconServiceResponse().print_populated_response(results)
