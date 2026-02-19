#!/usr/local/bin/python3
from datetime import datetime
from isodate import date_isoformat
from os import path
from pathlib import Path
from progress.bar import Bar

from bycon import (
    BYC,
    BYC_PARS,
    ByconDatasetResults,
    ByconMongo,
    ByconQuery,
    GenomeBins
)
from byconServiceLibs import (
    ask_limit_reset,
    assert_single_dataset_or_exit,
    set_collation_types,
    write_log
)

log_path = Path(path.join(log_path_root(), "analyses_statusmaps_logs"))
log_path.mkdir(parents=True, exist_ok=True)

"""

## `analysesStatusmapsRefresher`

"""

################################################################################
"""
* `bin/analysesStatusmapsRefresher.py -d progenetix -f "icdom-81703"`
* `bin/analysesStatusmapsRefresher.py`
  - default; new statusmaps for all `progenetix` analyses
"""
################################################################################

ask_limit_reset()
assert_single_dataset_or_exit()
set_collation_types()

ds_id           = BYC["BYC_DATASET_IDS"][0]
GB              = GenomeBins()
limit           = BYC_PARS.get("limit", 0)
cs_coll         = ByconMongo(ds_id).openMongoColl("analyses")
v_coll          = ByconMongo(ds_id).openMongoColl("variants")
record_queries  = ByconQuery().recordsQuery()

print(f'=> Using data values from {ds_id} for {GB.get_genome_bin_count()} intervals...')

ds_results = {}
if len(record_queries["entities"].keys()) > 0:
    DR = ByconDatasetResults(ds_id, record_queries)
    ds_results = DR.retrieveResults()

if not ds_results.get("analyses.id"):
    print(f'... collecting analysis id values from {ds_id} ...')
    ana_ids = []
    c_i = 0
    for ana in cs_coll.find( {} ):
        c_i += 1
        ana_ids.append(ana["id"])
        if limit > 0:
            if limit == c_i:
                break
else:
    ana_ids = ds_results["analyses.id"]["target_values"]

cs_no = len(ana_ids)

print(f'Re-generating statusmaps with {GB.get_genome_bin_count()} intervals for {cs_no} analyses...')
if "n" in input(f'Do you want to continue to update database **{ds_id}**?\n(Y|n): ').lower():
    exit()

counter     = 0
updated     = 0
duplicates  = []
no_cnv_type = 0

bar = Bar("{} analyses".format(ds_id), max = cs_no, suffix='%(percent)d%%'+" of "+str(cs_no) )

for ana_id in ana_ids:
    ana = cs_coll.find_one( { "id": ana_id } )
    _id = ana.get("_id")
    counter += 1
    if "EDAM:operation_3227" in ana.get("operation", {"id":"EDAM:operation_3961"}).get("id", "EDAM:operation_3961"):
        no_cnv_type += 1
        continue

    bar.next()
    cs_vars = v_coll.find({ "analysis_id": ana_id })
    maps, cs_cnv_stats, cs_chro_stats, dids = GB.getAnalysisFracMapsAndStats(cs_vars)
    if len(dids) > 0:
        duplicates += dids
    update_obj = {
        "info": ana.get("info", {}),
        "cnv_statusmaps": maps,
        "cnv_stats": cs_cnv_stats,
        "cnv_chro_stats": cs_chro_stats,
        "updated": datetime.now().isoformat()
    }

    if BYC.get("TEST_MODE", False) is True: 
        pass
    else:
        cs_coll.update_one( { "_id": _id }, { '$set': update_obj }  )
        updated += 1

    ############################################################################

bar.finish()

print(f"{counter} analyses were processed")
print(f"{no_cnv_type} analyses were not from CNV calling")
print(f'{updated} analyses were updated for\n    `cnv_statusmaps`\n    `cnv_stats`\n    `cnv_chro_stats`\nusing {GB.get_genome_bin_count()} bins ({BYC_PARS.get("genome_binning", "")})')

if len(duplicates) > 0:
    print(f'¡¡¡ {len(duplicates)} duplicate variant entries were found !!!')
    delete = input(f'Do you want to delete **{len(duplicates)}** duplicate variants?\n(y|N): ')
    if "y" in delete.lower():
        del_no = 0
        for v__id in duplicates:
            if BYC.get("TEST_MODE", False) is True:
                print(f'...would delete {v_coll.find_one( { "_id": v__id } )}')
            else:
                v_coll.delete_one( { "_id": v__id } )
                del_no += 1
        print(f'{del_no} duplicates were deleted')

log = BYC.get("WARNINGS", [])
write_log(log, path.join( log_path, "analyses_statusmaps" ))

