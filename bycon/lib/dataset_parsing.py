import re
from pymongo import MongoClient
from os import environ

from bycon_helpers import prdbug
from cgi_parsing import rest_path_value
from config import *

################################################################################

def select_dataset_ids():
    if ds_id_from_rest_path_value() is not False:
        return
    if ds_id_from_accessid() is not False:
        return
    if ds_id_from_record_id() is not False:
        return
    if ds_ids_from_form() is not False:
        return
    if ds_id_from_default() is not False:
        return


################################################################################

def ds_id_from_rest_path_value():
    ds_p_id = rest_path_value("datasets")
    if not ds_p_id:
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
    For data retrieval associated with a single record by its path id siuch as
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

    accessid = BYC_PARS.get("accessid", False)
    if any(x is False for x in [accessid]):
        return False

    ho_client = MongoClient(host=DB_MONGOHOST)
    h_o = ho_client[HOUSEKEEPING_DB][HOUSEKEEPING_HO_COLL].find_one({"id": accessid})
    if not h_o:
        return False
    ds_id = h_o.get("source_db", False)
    if ds_id is False:
        return False
    if ds_id not in BYC["DATABASE_NAMES"]:
        return False
    BYC.update({"BYC_DATASET_IDS":  ds_ids})
    return True


################################################################################

def ds_ids_from_form():
    f_ds_ids = BYC_PARS.get("dataset_ids", False)
    if f_ds_ids is False:
        return False
    ds_ids = []
    for ds_id in f_ds_ids:
        if ds_id in BYC["DATABASE_NAMES"]:
            ds_ids.append(ds_id)

    if len(ds_ids) < 1:
        return False
    BYC.update({"BYC_DATASET_IDS":  ds_ids})
    return True


################################################################################

def ds_id_from_default():
    defaults: object = BYC["beacon_defaults"].get("defaults", {})
    ds_id = defaults.get("default_dataset_id", "___undefined___")
    if ds_id not in BYC["DATABASE_NAMES"]:
        return False
    BYC.update({"BYC_DATASET_IDS": [ ds_id ]})
    return True


