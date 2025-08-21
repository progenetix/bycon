#!/usr/local/bin/python3

from bycon import *
from datetime import datetime
from progress.bar import Bar
from pymongo import MongoClient

from byconServiceLibs import (
    assert_single_dataset_or_exit,
    log_path_root,
    write_log
)

"""

"""

################################################################################
################################################################################
################################################################################

ds_id = assert_single_dataset_or_exit()

data_client = MongoClient(host=DB_MONGOHOST)
var_coll = data_client[ds_id]["variants"]

mode = str(BYC_PARS.get("mode"))
supported_modes = ["Allele", "CopyNumberChange", "Adjacency"]

if mode not in supported_modes:
    print(f"Mode '{mode}' is not supported.\nSupported modes are: {supported_modes} and the current mode should be indicated with e.g.\n`--mode {supported_modes[0]}`.")
    print 
    exit()

q = {"type": mode}

v_no = var_coll.count_documents(q)

if not BYC["TEST_MODE"]:
    print(f"Found {v_no} variants of type '{mode}' in dataset '{ds_id}'.")
    if not "y" in input(f"Do you **really* want to VRSify {v_no} variants?\n(y|N): "):
        exit()

if not BYC["TEST_MODE"]:
    bar = Bar(f'VRSifying {mode} ', max = v_no, suffix='%(percent)d%%'+" of "+str(v_no) )      

i = 0
BV = ByconVariant()
for v in var_coll.find(q):
    if not BYC["TEST_MODE"]:
        bar.next()
    i += 1
    if BYC["TEST_MODE"] and i > BYC_PARS.get("test_mode_count"):
      break
    _id = v.get("_id")
    byc_id = f'bycvar-{_id}'
    vrs_v = BV.vrsVariant(v)
    if (e := vrs_v.get("ERROR")):
        print(e)
        continue
    vrs_v.update({
        "id": byc_id,
        "updated": datetime.now().isoformat()
    })
    if not BYC["TEST_MODE"]:
        var_coll.update_one({"_id": _id}, { "$set": vrs_v })
    else:
        print(i)
        prjsonnice(vrs_v)

if not BYC["TEST_MODE"]:
    bar.finish()
