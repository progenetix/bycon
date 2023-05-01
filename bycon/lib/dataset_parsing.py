import re
from pymongo import MongoClient

from cgi_parsing import *

################################################################################

def select_dataset_ids(byc):

    if not "dataset_ids" in byc.keys():
        byc.update( { "dataset_ids": [ ] } )

    if ds_id_from_rest_path_value(byc) is not False:
        return byc

    if ds_id_from_accessid(byc) is not False:
        return byc            

    if ds_ids_from_form(byc) is not False:
        return byc            
    
    if ds_ids_from_args(byc) is not False:
        return byc            

    return byc

################################################################################

def ds_id_from_rest_path_value(byc):

    ds_id = rest_path_value("datasets")
    if ds_id == "empty_value":
        return False

    if ds_id not in byc["dataset_definitions"].keys():
        return False

    byc.update( { "dataset_ids": [ ds_id ] } )
    return byc

################################################################################

def ds_id_from_accessid(byc):

    # TODO: This is very verbose. In principle there should be an earlier
    # test of existence...

    accessid = byc["form_data"].get("accessid", False)
    if "accessid" is False:
        return False

    info_db = byc["config"].get("info_db", False)
    if "info_db" is False:
        return False

    ho_collname = byc["config"].get("handover_coll", False)
    if "ho_collname" is False:
        return False

    ho_client = MongoClient()
    h_o = ho_client[ info_db ][ ho_collname ].find_one( { "id": accessid } )
    if not h_o:
        return False

    ds_id = h_o.get("source_db", False)
    if "ds_id" is False:
        return False

    if ds_id not in byc["dataset_definitions"].keys():
        return False

    byc.update( { "dataset_ids": [ ds_id ] } )
    return byc

################################################################################

def ds_ids_from_form(byc):

    f_ds_ids = byc["form_data"].get("dataset_ids", False)
    if f_ds_ids is False:
        return False

    ds_ids = [ ]
    for ds_id in f_ds_ids:
        if ds_id in byc["dataset_definitions"].keys():
            ds_ids.append(ds_id)

    if len(ds_ids) < 1:
        return False

    byc.update( { "dataset_ids": ds_ids } )
    
    return byc

################################################################################

def ds_ids_from_args(byc):

    if not "args" in byc or byc["args"] is None:
        return byc

    if byc["args"].datasetIds:
        ds_ids = re.split(",", byc["args"].datasetIds)
        byc.update( { "dataset_ids": ds_ids } )
        return byc

    return byc
