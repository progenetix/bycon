import pymongo
import re

from bycon.lib.cgi_parsing import rest_path_value


################################################################################

def select_dataset_ids(byc):
    if "dataset_ids" not in byc.keys():
        byc.update({"dataset_ids": []})

    if ds_id_from_rest_path_value(byc) is not False:
        return
    if ds_id_from_accessid(byc) is not False:
        return
    if ds_ids_from_form(byc) is not False:
        return
    if ds_ids_from_args(byc) is not False:
        return

    ################################################################################


def ds_id_from_rest_path_value(byc):
    ds_id = rest_path_value("datasets")

    if ds_id not in byc["dataset_definitions"].keys():
        return False

    byc.update({"dataset_ids": [ds_id]})
    return True


################################################################################

def ds_id_from_accessid(byc):
    # TODO: This is very verbose. In principle there should be an earlier
    # test of existence...

    accessid = byc["form_data"].get("accessid", False)
    services_db = byc["config"].get("services_db", False)
    ho_collname = byc["config"].get("handover_coll", False)

    if any(x is False for x in [accessid, services_db, ho_collname]):
        return False

    ho_client = pymongo.MongoClient()
    h_o = ho_client[services_db][ho_collname].find_one({"id": accessid})
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
    f_ds_ids = byc["form_data"].get("dataset_ids", False)
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

def ds_ids_from_args(byc):
    if "args" not in byc or byc["args"] is None:
        return False

    if byc["args"].datasetIds:
        ds_ids = re.split(",", byc["args"].datasetIds)
        byc.update({"dataset_ids": ds_ids})
        return True

    return False
