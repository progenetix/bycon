import re, sys

from datetime import datetime

from os import environ, path
from pymongo import MongoClient
from copy import deepcopy

# services_lib_path = path.join( path.dirname( path.abspath(__file__) ) )
# sys.path.append( services_lib_path )
from config import *
from bycon_helpers import prdbug, return_paginated_list
from interval_utils import GenomeBins

################################################################################
################################################################################
################################################################################

class ByconSummary():
    """
    # The `ByconSummary` class

    """

    def __init__(self):
        self.errors = []
        self.min_number = BYC_PARS.get("min_number", 0)
        self.intervalFrequenciesBundle = {}
        self.limit = BYC_PARS.get("limit", 0)
        self.skip = BYC_PARS.get("skip", 0)


    #--------------------------------------------------------------------------#
    #----------------------------- public -------------------------------------#
    #--------------------------------------------------------------------------#

    def analyses_frequencies_bundle(self, ds_id="___none___", analyses_result={}):
        self.analyses_result = analyses_result
        self.ds_id = ds_id
        self.__analyses_bundle_analyses_result()
        return self.intervalFrequenciesBundle


    #--------------------------------------------------------------------------#
    #----------------------------- private ------------------------------------#
    #--------------------------------------------------------------------------#

    def __analyses_bundle_analyses_result(self, label=""):
        sample_coll = MongoClient(host=DB_MONGOHOST)[self.ds_id]["analyses"]
        s_ids = self.analyses_result.get("target_values", [])
        r_no = len(s_ids)
        s_ids = return_paginated_list(s_ids, self.skip, self.limit)

        prdbug(f'... __analyses_bundle_analyses_result {self.ds_id} => {r_no} samples, limit: {self.limit}, after: {len(s_ids)}')

        analysis_bundle = []
        GB = GenomeBins()
        self.intervalFrequenciesBundle = {
            "dataset_id": self.ds_id,
            "group_id": self.ds_id,
            "label": label,
            "sample_count": 0,
            "interval_frequencies": []
        }

        for s_id in s_ids:
            s = sample_coll.find_one({"id": s_id })

            cnv_statusmaps = s.get("cnv_statusmaps", False)

            if cnv_statusmaps is False:
                continue

            analysis_bundle.append({
                "dataset_id": self.ds_id,
                "analysis_id": s.get("id", "NA"),
                "biosample_id": s.get("biosample_id", "NA"),
                "label": s.get("label", s.get("biosample_id", "")),
                "cnv_statusmaps": cnv_statusmaps
            })

        intervals, cnv_ana_count = GB.intervalFrequencyMaps(analysis_bundle)
        self.intervalFrequenciesBundle .update({"sample_count": cnv_ana_count})

        if cnv_ana_count < self.min_number:
            return

        for intv_i, intv in enumerate(intervals):
            self.intervalFrequenciesBundle["interval_frequencies"].append(intv.copy())
        prdbug(f'... __analysisBundleCreateIsets {self.ds_id} => sample_count {cnv_ana_count} ...')


