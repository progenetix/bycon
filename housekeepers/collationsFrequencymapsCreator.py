#!/usr/local/bin/python3

import time
import random

from progress.bar import Bar

from bycon import (
    BYC, BYC_DBS, BYC_PARS, ByconDatasetResults, ByconQuery, ByconMongo, CollationQuery, prdbug
)
from byconServiceLibs import (
    assert_single_dataset_or_exit,
    ask_limit_reset,
    ByconBundler,
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

def main():

    ask_limit_reset()
    dataset_id          = assert_single_dataset_or_exit()    
    script_start_time   = time.time()
    print(f'=> Using data values from {dataset_id}...')

    BCF         = ByconCollationsAddFrequencies(dataset_id)
    coll_ids    = BCF.collationsRetrieveIds()
    coll_no     = len(coll_ids)
    print(f'=> Processing {len(coll_ids)} collations from {dataset_id}...')

    skip_existing = False
    if "skip" in (BYC_PARS.get("mode", "")).lower():
        skip_existing = True
        print(f'=> Skipping existing frequencymaps: {skip_existing}')

    if not BYC["TEST_MODE"]:
        bar = Bar(f'{dataset_id} fMaps', max = coll_no, suffix='%(percent)d%%'+f' of {coll_no}' )

    # ---------------------- collations loop --------------------------------- #

    coll_coll = BCF.openCollationCollection()

    for c_id in coll_ids:
        collation   = coll_coll.find_one({"id": c_id})
        c_o_id      = collation.get("_id")
        if skip_existing is True:
            if "frequencymap" in collation:
                if not BYC["TEST_MODE"]:
                    bar.next()
                continue

        start_time      = time.time()
        frequencymap    = BCF.collationGetFrequencyMap(collation)
        ana_no          = frequencymap.get("frequencymap_samples", 0)

        if ana_no < 1:
            print(f'\n... no CNV analyses for {c_id} => skipping update')
            if not BYC["TEST_MODE"]:
                bar.next()
            continue

        update_obj  = {
            "cnv_analyses": ana_no,
            "frequencymap": frequencymap
        }

        if ana_no > 5000:
            proc_time = time.time() - start_time
            print(f'\n==> Processed {c_id}: {ana_no} in {"%.2f" % proc_time}s: {"%.4f" % (proc_time/ana_no)}s per analysis')

        if not BYC["TEST_MODE"]:
            coll_coll.update_one({"_id": c_o_id}, {"$set": update_obj})
            bar.next()       
 
    # --------------------- / collations loop -------------------------------- #

    if not BYC["TEST_MODE"]:
        bar.finish()

    script_duration = (time.time() - script_start_time) / 60

    print(f'\n==> Total run time was ~{"%.0f" %  script_duration} minutes')

################################################################################

class ByconCollationsAddFrequencies:
    def __init__(self, dataset_id):
        self.dataset_id = dataset_id
        GB = GenomeBins()
        self.GenomeBins = GB
        self.interval_count = GB.get_genome_bin_count()
        self.binning = GB.get_genome_binning()
        self.limit = BYC_PARS.get("limit", 200)
        self.coll_coll = ByconMongo().openMongoColl(dataset_id, BYC_DBS["collections"]["collation"])

    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def openCollationCollection(self):
        return self.coll_coll

    #--------------------------------------------------------------------------#

    def collationsRetrieveIds(self):
        query = {}
        if len(BYC_PARS.get("filters", [])) > 0 or len(BYC_PARS.get("collation_types", [])) > 0:
            query = CollationQuery().getQuery()
        coll_ids = self.coll_coll.distinct("id", query)
        random.shuffle(coll_ids)
        return coll_ids

    #--------------------------------------------------------------------------#

    def collIdGetFrequencyMap(self, coll_id):
        collation = self.coll_coll.find_one({"id": coll_id})
        if not collation:
            print(f'!!! no collation found for {coll_id} !!!')
            return {}, 0
        return self.__collation_generate_frequencymap(collation)

    #--------------------------------------------------------------------------#

    def collationGetFrequencyMap(self, collation):
        return self.__collation_generate_frequencymap(collation)

    #--------------------------------------------------------------------------#
    #---------------------------- private -------------------------------------#
    #--------------------------------------------------------------------------#

    def __collation_generate_frequencymap(self, collation):
        c_id = collation.get("id")
        BYC_PARS.update({"filters":[{"id": c_id}]})

        for exc_f in collation.get("cnv_excluded_filters", []):
            BYC_PARS["filters"].append({"id": exc_f, "excluded": True})
            prdbug(f'... {c_id} excluding {exc_f}')
        for inc_f in collation.get("cnv_required_filters", []):
            prdbug(f'... {c_id} requiring {inc_f}')
            BYC_PARS["filters"].append({"id": inc_f})

        record_queries  = ByconQuery().recordsQuery()
        DR              = ByconDatasetResults(self.dataset_id, record_queries)
        ds_results      = DR.retrieveResults()

        if not "analyses.id" in ds_results:
            print(f'\n!!! no results for {c_id} in {self.dataset_id} !!!')
            print(f'\n... ds_results keys: {list(ds_results.keys())}')
            return {}
        ana_ids         = ds_results["analyses.id"]["target_values"]
        if len(ana_ids) < 1:
            return {}

        if self.limit > 0 and len(ana_ids) > self.limit:
            ana_ids = random.sample(ana_ids, self.limit)

        prdbug(f'\n... after limit {len(ana_ids)}')
        query       = {"id": {"$in": ana_ids}, "operation.id": "EDAM:operation_3961"}
        ana_cursor  = ByconMongo().resultCursorFromQuery(self.dataset_id, "analyses", query, {"_id": 0})
        intervals, cnv_ana_count = self.GenomeBins.intervalFrequencyMaps(ana_cursor)
        prdbug(f'... retrieved {cnv_ana_count} CNV analyses')

        return {
            "interval_count": self.interval_count,
            "binning": self.binning,
            "intervals": intervals,
            "frequencymap_samples": cnv_ana_count
        }

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()

