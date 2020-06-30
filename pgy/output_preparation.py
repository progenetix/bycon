from pymongo import MongoClient
import re

################################################################################
################################################################################
################################################################################

def callsets_add_metadata(ds_id, cs, **kwargs):

    io_prefixes = kwargs[ "config" ][ "io_prefixes" ]

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ ds_id ]
    mongo_coll = mongo_db[ 'biosamples' ]
    
    bios = mongo_coll.find_one({"id": cs["biosample_id"] })

    if bios:
        for pre in io_prefixes:
            pre_id, pre_lab = get_id_label_for_prefix(bios["biocharacteristics"]+bios["external_references"], pre, **kwargs)
            cs[ pre+"::id" ] = pre_id
            if not pre_lab:
                pre_lab = str("")
            cs[ pre+"::label" ] = pre_lab

    return cs

################################################################################

def get_id_label_for_prefix(data_list, prefix, **kwargs):

    pre_id = ""
    pre_lab = ""
    for item in data_list:
        if re.compile( r"^"+prefix+r"[\:\-]" ).match(item["type"]["id"]):
            pre_id = item["type"]["id"]
            if "label" in item["type"]:
                pre_lab = item["type"]["label"]

    return(pre_id, pre_lab)
