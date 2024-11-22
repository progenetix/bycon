#!/usr/bin/env python3

import datetime, time
from pymongo import MongoClient
from progress.bar import Bar
from random import shuffle as random_shuffle

from bycon import *
from byconServiceLibs import (
    assertSingleDatasetOrExit,
    ask_limit_reset,
    ByconBundler,
    CollationQuery,
    GenomeBins,
    set_collation_types
)

################################################################################

def main():
    ask_limit_reset()
    ds_id = assertSingleDatasetOrExit()
    GB = GenomeBins()
    interval_count = GB.get_genome_bin_count()
    binning = GB.get_genome_binning()
    print(f'=> Using data values from {ds_id} for {interval_count} intervals...')

    if "skip" in (BYC_PARS.get("mode", "")).lower():
        skip_existing = True
    else:
        skip_existing = False

    BYC.update({"PAGINATED_STATUS": False})

    data_client = MongoClient(host=DB_MONGOHOST)
    data_db = data_client[ ds_id ]
    coll_coll = data_db[ "collations" ]
    ind_coll = data_db["individuals"]
    bios_coll = data_db[ "biosamples" ]
    cs_coll = data_db["analyses"]

    query = {}
    if len(BYC_PARS.get("filters", [])) > 0 or len(BYC_PARS.get("collation_types", [])) > 0:
        query = CollationQuery().getQuery()
    coll_ids = coll_coll.distinct("id", query)
    random_shuffle(coll_ids)
    coll_no = len(coll_ids)

    print(f'=> Processing {len(coll_ids)} collations from {ds_id}...')

    if not BYC["TEST_MODE"]:
        bar = Bar(f'{coll_no} {ds_id} fMaps', max = coll_no, suffix='%(percent)d%%'+f' of {coll_no}' )

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
        coll = coll_coll.find_one({"id": c_id})
        c_o_id = coll.get("_id")
        if not coll:
            print(f"\n¡¡¡ some error - collation {c_id} not found !!!")
            if not BYC["TEST_MODE"]:
                bar.next()
            continue

        if not BYC["TEST_MODE"]:
            bar.next()

        if skip_existing is True:
            if "frequencymap" in coll:
                prdbug(f'\n... skipping {c_id} with existing frequencymap')
                continue

        start_time = time.time()

        BYC.update({"BYC_FILTERS":[{"id":c_id}, {"id": "EDAM:operation_3961"}]})
        BYC.update({"FMAPS_SCOPE": coll.get("scope", "biosamples")})
        
        prdbug(f'\n=> processing {c_id} with limit {BYC_PARS.get("limit")}')
        RSS = ByconResultSets().datasetsResults()
        pdb = ByconBundler().resultsets_frequencies_bundles(RSS)
        if_bundles = pdb.get("interval_frequencies_bundles")

        if len(if_bundles) < 1:
            prdbug(f'No interval_frequencies for {c_id}')
            continue

        analyses_count = RSS[ds_id]["analyses.id"]["target_count"]
        cnv_cs_count = if_bundles[0].get("sample_count", 0)

        if cnv_cs_count < 1:
            continue

        update_obj = {
            "cnv_analyses": analyses_count,
            "frequencymap": {
                "interval_count": interval_count,
                "binning": binning,
                "intervals": if_bundles[0].get("interval_frequencies", []),
                "frequencymap_samples": cnv_cs_count,
                "cnv_analyses": analyses_count
            }
        }

        if cnv_cs_count > 2000:
            proc_time = time.time() - start_time
            print(f'\n==> Processed {c_id}: {cnv_cs_count} of {analyses_count} in {"%.2f" % proc_time}s: {"%.4f" % (proc_time/cnv_cs_count)}s per analysis')

        if not BYC["TEST_MODE"]:
            coll_coll.update_one(
            {"_id": c_o_id},
            {"$set": update_obj}
        )
    
    if not BYC["TEST_MODE"]:
        bar.finish()


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
