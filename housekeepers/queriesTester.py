#!/usr/bin/env python3

from bycon import *
from pymongo import MongoClient

from bycon import byconServiceLibs
from service_helpers import assertSingleDatasetOrExit


"""
"""

################################################################################
################################################################################
################################################################################

ds_id = assertSingleDatasetOrExit()
BYC_PARS.update({"response_entity_path_id":"analyses"})
set_entities()
for qek, qev in BYC.get("test_queries", {}).items():
    for p, v in qev.items():
        if p == "filters":
            f_l = []
            for f in v:
                f_l.append({"id": f})
            if len(f_l) > 0:
                BYC.update({"BYC_FILTERS":f_l})
        else:
            BYC_PARS.update({p: v})

    # print(f'... getting data for {qek}')
    BRS = ByconResultSets()
    r_c = BRS.get_record_queries()
    ds_results = BRS.datasetsResults()
    # print(f'... got it')

    # clean out those globals for next run
    # filters are tricky since they have a default `[]` value
    # and have been pre-parsed into BYC_FILTERS at the stage of
    # `ByconResultSets()` (_i.e._ embedded `ByconQuery()`)
    for p, v in qev.items():
        if p == "filters":
            BYC_PARS.update({"filters": []})
        else:
            BYC_PARS.pop(p)
    BYC.update({"BYC_FILTERS": []})
    
    if not (ds := ds_results.get(ds_id)):
        print(f'ERROR - no {qek} data for {ds_id}')
        prjsonnice(r_c)
        continue
    if BYC.get("DEBUG_MODE"):
        print(f'############################### {qek} ###############################')
        prjsonnice(r_c)

    print(f'==> {qek} with {ds["analyses.id"].get("target_count")} analysis hits')

