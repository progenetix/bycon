import re
from pymongo import MongoClient
from os import environ

from bycon_helpers import prdbug
from cgi_parsing import rest_path_value
from config import *

################################################################################

def select_dataset_ids():
    if ds_id_from_rest_path_value():
        return
    if ds_id_from_accessid():
        return
    if ds_id_from_record_id():
        return
    if ds_ids_from_form():
        return
    if ds_id_from_default():
        return


################################################################################

def ds_id_from_rest_path_value():
    if not (ds_p_id := rest_path_value("datasets")):
        return False

    ds_ids = []
    for ds_id in ds_p_id.split(","):
        if ds_id in BYC["DATABASE_NAMES"]:
            ds_ids.append(ds_id)

    if len(ds_ids) < 1:
        return False

    BYC.update({"BYC_DATASET_IDS":  ds_ids})
    return True


################################################################################

def ds_id_from_record_id():
    """
    For data retrieval associated with a single record by its path id such as
    `biosamples/{id}` the default Beacon model does not provide any way to provide
    the associated dataset id with the request. The assumption is that any record
    id is unique across all datasets.
    This function is a placeholder for a solution:
    * retrieve the dataset id from the record id, e.g. by having a specific prefix
      or pattern in the record id, associated for a specific dataset (a bit of a fudge...)
    * access a lookup database for the id -> datasetId matches
    """
    return False


################################################################################

def ds_id_from_accessid():
    # TODO: This is very verbose. In principle there should be an earlier
    # test of existence...

    if not (accessid := BYC_PARS.get("accessid")):
        return False

    ho_client = MongoClient(host=DB_MONGOHOST)
    h_o = ho_client[HOUSEKEEPING_DB][HOUSEKEEPING_HO_COLL].find_one({"id": accessid})
    if not h_o:
        return False
    ds_id = h_o.get("source_db", False)
    if (ds_id := str(h_o.get("source_db"))) not in BYC["DATABASE_NAMES"]:
        return False
    BYC.update({"BYC_DATASET_IDS":  [ds_id]})
    return True


################################################################################

def ds_ids_from_form():
    
    if not (f_ds_ids := BYC_PARS.get("dataset_ids")):
        return False
    ds_ids = [ds for ds in f_ds_ids if ds in BYC.get("DATABASE_NAMES",[])]
    if len(ds_ids) > 0:
        BYC.update({"BYC_DATASET_IDS":  ds_ids})
        return True
    return False


################################################################################

def ds_id_from_default():
    defaults: object = BYC["beacon_defaults"].get("defaults", {})  
    if (ds_id := str(defaults.get("default_dataset_id"))) not in BYC["DATABASE_NAMES"]:
        return False
    BYC.update({"BYC_DATASET_IDS": [ ds_id ]})
    return True


