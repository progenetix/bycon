import re
from pymongo import MongoClient
from os import environ

from bycon_helpers import prdbug
from cgi_parsing import rest_path_value
from config import *

################################################################################

def select_dataset_ids(byc):
    byc.update({"dataset_ids": []})
    if ds_id_from_rest_path_value(byc) is not False:
        return
    if ds_id_from_accessid(byc) is not False:
        return
    if ds_ids_from_form(byc) is not False:
        return
    if ds_id_from_default(byc) is not False:
        return


################################################################################

def ds_id_from_rest_path_value(byc):
    ds_id = rest_path_value("datasets")
    if ds_id is None:
        return False

    if ds_id not in byc["dataset_definitions"].keys():
        return False

    byc.update({"dataset_ids": [ds_id]})
    return True


################################################################################

def ds_id_from_accessid(byc):
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
    if ds_id not in byc["dataset_definitions"].keys():
        return False
    byc.update({"dataset_ids": [ds_id]})
    return True


################################################################################

def ds_ids_from_form(byc):
    f_ds_ids = BYC_PARS.get("dataset_ids", False)
    if f_ds_ids is False:
        return False
    ds_ids = []
    for ds_id in f_ds_ids:
        if ds_id in byc["dataset_definitions"].keys():
            ds_ids.append(ds_id)

    if len(ds_ids) < 1:
        return False
    byc.update({"dataset_ids": ds_ids})
    return True


################################################################################

def ds_id_from_default(byc):
    ds_id = byc.get("default_dataset_id", "___undefined___")
    if ds_id not in byc["dataset_definitions"].keys():
        return False
    byc.update({"dataset_ids": [ ds_id ]})
    return True


