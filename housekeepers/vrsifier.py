#!/usr/local/bin/python3

from bycon import *
from pymongo import MongoClient
from progress.bar import Bar

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
print(mode)

if mode not in ["Allele", "CopyNumberChange"]:
    exit()

q = {"type":mode}

v_no = var_coll.count_documents(q)

if not BYC["TEST_MODE"]:
    bar = Bar(f'VRSifying {mode} ', max = v_no, suffix='%(percent)d%%'+" of "+str(v_no) )      

i = 0
BV = ByconVariant()
for v in var_coll.find(q):
    if not BYC["TEST_MODE"]:
        bar.next()
    i += 1
    if i > 5:
      break
    _id = v.get("_id")
    vrs_v = BV.vrsVariant(v)
    if (e := vrs_v.get("ERROR")):
        print(e)
        continue 
    if not BYC["TEST_MODE"]:
        var_coll.update_one({"_id": _id}, { "$set": vrs_v })
    else:
        print(i)
        prjsonnice(vrs_v)

if not BYC["TEST_MODE"]:
    bar.finish()
