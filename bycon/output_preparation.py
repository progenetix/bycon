from pymongo import MongoClient
import re

################################################################################
################################################################################
################################################################################

def callsets_add_metadata(cs, **kwargs):

    dataset_id = kwargs[ "config" ][ "data_pars" ][ "dataset_id" ]
    bio_prefixes = kwargs[ "config" ][ "bio_prefixes" ]

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ dataset_id ]
    mongo_coll = mongo_db[ 'biosamples' ]
    
    for bio_pre in bio_prefixes:
        cs[bio_pre] = ""

    bios = mongo_coll.find_one({"id": cs["biosample_id"] })

    if bios:
        for biocharacteristic in bios["biocharacteristics"]:
            for bio_pre in bio_prefixes:
                if re.compile( '^'+bio_pre ).match(biocharacteristic["type"]["id"]):
                    cs[ bio_pre+"::id" ] = biocharacteristic["type"]["id"]
                    cs[ bio_pre+"::label" ] = biocharacteristic["type"]["label"]
    return cs

################################################################################

def get_id_label_for_prefix(data_list, prefix, **kwargs):

    pre_id = ""
    pre_lab = ""
    for item in data_list:
        if re.compile( r"^"+prefix+r"[\:\-]" ).match(item["type"]["id"]):
            pre_id = item["type"]["id"]
            pre_lab = item["type"]["label"]

    return(pre_id, pre_lab)
