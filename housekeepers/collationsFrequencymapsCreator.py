#!/usr/local/bin/python3

import time
from pymongo import MongoClient
from progress.bar import Bar
from random import shuffle as random_shuffle

from bycon import *
from byconServiceLibs import (
    assert_single_dataset_or_exit,
    ask_limit_reset,
    ByconBundler,
    CollationQuery,
    GenomeBins,
    set_collation_types
)

"""
The `collationsFrequencymapsCreator.py` script is used to create frequency maps
from the CNV status maps in the `analysis` records. It is an essential part of
a fully functional `bycon` database setup if this includes CNV data and should be
run after any content changes (new data or changing of collations / filters).

The script will add `frequencymap` object to each of the collations.

#### Examples

* `./collationsFrequencymapsCreator.py -d examplez`
* `./collationsFrequencymapsCreator.py -d examplez --mode "skip existing"`
* `./collationsFrequencymapsCreator.py -d examplez --collationTypes "pubmed,icdom,icdot"`

"""

ask_limit_reset()
limit = BYC_PARS.get("limit", 200)
ds_id = assert_single_dataset_or_exit()
GB = GenomeBins()
interval_count = GB.get_genome_bin_count()
binning = GB.get_genome_binning()
script_start_time = time.time()
print(f'=> Using data values from {ds_id} for {interval_count} intervals...')

if "skip" in (BYC_PARS.get("mode", "")).lower():
    skip_existing = True
else:
    skip_existing = False

print(f'=> Skipping existing frequencymaps: {skip_existing}')

BYC.update({"PAGINATED_STATUS": False})

data_client = MongoClient(host=DB_MONGOHOST)
data_db = data_client[ ds_id ]
coll_coll = data_db[ "collations" ]
cs_coll = data_db["analyses"]

query = {}
if len(BYC_PARS.get("filters", [])) > 0 or len(BYC_PARS.get("collation_types", [])) > 0:
    query = CollationQuery().getQuery()
coll_ids = coll_coll.distinct("id", query)
random_shuffle(coll_ids)
coll_no = len(coll_ids)

print(f'=> Processing {len(coll_ids)} collations from {ds_id}...')

if not BYC["TEST_MODE"]:
    bar = Bar(f'{ds_id} fMaps', max = coll_no, suffix='%(percent)d%%'+f' of {coll_no}' )

# this just counts the number of collations with existing frequencymaps
# and adjusts the progress bar accordingly (including a fancy delayed growth...)
if skip_existing is True:
    query.update({"frequencymap": {"$exists": True}})
    coll_i = coll_coll.count_documents(query)
    if not BYC["TEST_MODE"]:
        for i in range(coll_i):
            time.sleep(0.001)
            bar.next()

for c_id in coll_ids:

    prdbug(c_id)

    coll = coll_coll.find_one({"id": c_id})
    c_o_id = coll.get("_id")
    if not coll:
        print(f"\n¡¡¡ some error - collation {c_id} not found !!!")
        if not BYC["TEST_MODE"]:
            bar.next()
        continue

    if skip_existing is True:
        if "frequencymap" in coll:
            prdbug(f'\n... skipping {c_id} with existing frequencymap')
            continue

    start_time = time.time()
    BYC_PARS.update({"filters":[{"id": c_id}]})
    for exc_f in coll.get("cnv_excluded_filters", []):
        BYC_PARS["filters"].append({"id": exc_f, "excluded": True})
        prdbug(f'... {c_id} excluding {exc_f}')
    for inc_f in coll.get("cnv_required_filters", []):
        prdbug(f'... {c_id} requiring {inc_f}')
        BYC_PARS["filters"].append({"id": inc_f})

    record_queries = ByconQuery().recordsQuery()
    DR = ByconDatasetResults(ds_id, record_queries)
    ds_results = DR.retrieveResults()
    if not "analyses.id" in ds_results:
        print(f'!!! no results for {c_id} !!!')
        print(f'\n... ds_results keys: {list(ds_results.keys())}')
        continue
    ana_ids = ds_results["analyses.id"]["target_values"]
    prdbug(f'...{len(ana_ids)} matched analyses')
    if not BYC["TEST_MODE"]:
        bar.next()

    if len(ana_ids) < 1:
        continue

    ana_ids = return_paginated_list(ana_ids, 0, limit)
    prdbug(f'\n... after limit {len(ana_ids)}')

    intervals, cnv_ana_count = GB.intervalAidFrequencyMaps(ds_id, ana_ids)
    prdbug(f'... retrieved {cnv_ana_count} CNV analyses')

    if cnv_ana_count < 1:
        continue

    update_obj = {
        "cnv_analyses": cnv_ana_count,
        "frequencymap": {
            "interval_count": interval_count,
            "binning": binning,
            "intervals": intervals,
            "frequencymap_samples": cnv_ana_count
        }
    }

    if cnv_ana_count > 5000:
        proc_time = time.time() - start_time
        print(f'\n==> Processed {c_id}: {cnv_ana_count} in {"%.2f" % proc_time}s: {"%.4f" % (proc_time/cnv_ana_count)}s per analysis')

    if not BYC["TEST_MODE"]:
        coll_coll.update_one(
        {"_id": c_o_id},
        {"$set": update_obj}
    )

if not BYC["TEST_MODE"]:
    bar.finish()

script_duration = (time.time() - script_start_time) / 60

print(f'\n==> Total run time was ~{"%.0f" %  script_duration} minutes')
