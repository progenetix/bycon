import json
from pymongo import MongoClient
from bson.objectid import ObjectId

from cgi_utils import *
from variant_responses import *

################################################################################

def retrieve_biosamples(ds_id, byc):

    bio_s = [ ]

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]

    ds_results = byc["dataset_results"][ds_id]

    bio_s = retrieve_biosamples_from_biosample__ids(data_db, ds_results["biosamples._id"][ "target_values" ])

    return bio_s

################################################################################

def retrieve_biosamples_from_biosample__ids(data_db, bs__ids):

    bio_s = [ ]
    for bs__id in bs__ids:
        bio_s.append( data_db["biosamples"].find_one({"_id": ObjectId(bs__id)}) ) 

    return bio_s

################################################################################

def retrieve_biosamples_from_biosample_ids(data_db, bs_ids):

    bio_s = [ ]
    for bs_id in bs_ids:
        bio_s.append( data_db["biosamples"].find_one({"_id": bs_id}) )

    return bio_s

################################################################################

def retrieve_biosamples_for_individuals(data_db, ind_s):

    bio_s = [ ]
    for ind in ind_s:
        bio_s += retrieve_biosamples_from_individual_id(data_db, ind["id"])

    return bio_s

###############################################################################

def retrieve_biosamples_from_individual_id(data_db, ind_id):

    bio_curs = data_db["biosamples"].find({"individual_id":ind_id})

    return list(bio_curs)

################################################################################

def retrieve_biosamples_for_variants(data_db, vs):

    bio_s = [ ]
    for v in vs:
        if "biosample_id" in v:
            bio_s.append( data_db["biosamples"].find_one({"id": v["biosample_id"]}) )

    return bio_s
