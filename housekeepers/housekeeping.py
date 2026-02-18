#!/usr/local/bin/python3

import re, json, yaml, sys
from datetime import datetime
from isodate import date_isoformat
from os import path, environ, pardir, system
from progress.bar import Bar

from bycon import *
from byconServiceLibs import *

loc_path = path.dirname( path.abspath(__file__) )

################################################################################
################################################################################
################################################################################

def main():
    set_collation_types()
    ask_limit_reset()

    ds_id = assert_single_dataset_or_exit()

    # collecting the actions
    todos = {
        "mongodb_index_creation": input("Check & refresh MongoDB indexes?\n(y|N): "),
        "logical_sex_assignments": input("Assign logical sex values from biosample histologies etc. in individuals?\n(y|N): "),
        "individual_times_days": input("Update Individual helper params (`age_days`, `followup_days`, `index_disease`...)?\n(y|N): "),
        "analyses_labels": input("Create/update `label` field for analyses, from biosamples?\n(y|N): "),
        "update_variants": input("Update variants to latest format (VRS v2)?\n(y|N): "),
        "update_cs_statusmaps": input(f'Update statusmaps in `analyses` for {ds_id}?\n(y|N): '),
        "update_collations": input(f'Create `collations` for {ds_id}?\n(Y|n): '),
        "update_frequencymaps": input(f'Create `frequencymaps` for {ds_id} collations?\n(Y|n): '),
        "datasets_counts": input("Recalculate counts for all datasets?\n(y|N): "),
        "geolocs_updates": input("Relabel all biosamples with existing geolocation?\n(y|N): ")
    }

    m_h         = BYC_DBS["mongodb_host"]
    m_d         = BYC_DBS["services_db"]
    data_db     = ByconMongo(ds_id).openMongoDatabase()
    services_db = ByconMongo(m_d).openMongoDatabase()

    ana_coll    = data_db[ BYC_DBS.get("collections", {}).get("analysis")   ]
    ind_coll    = data_db[ BYC_DBS.get("collections", {}).get("individual") ]
    bios_coll   = data_db[ BYC_DBS.get("collections", {}).get("biosample")  ]

    #>-------------------- MongoDB index updates -----------------------------<#

    if "y" in todos.get("mongodb_index_creation", "n").lower():
        print(f'\n{__hl()}==> updating indexes for {ds_id}"')
        system(f'{loc_path}/mongodbIndexer.py -d {ds_id}')

    #>------------------- / MongoDB index updates ----------------------------<#

    #>------------------------- biosamples -----------------------------------<#

    #>------------------------ geo locations ---------------------------------<#

    if "y" in todos.get("geolocs_updates", "n").lower():
        ByconGeoResource().update_geolocations(ds_id, "biosamples")

    #>----------------------- / biosamples -----------------------------------<#

    #>------------------------- analyses -------------------------------------<#

    if "y" in todos.get("analyses_labels", "n").lower():
        cs_query = {}
        no = ana_coll.count_documents(cs_query)

        if not BYC["TEST_MODE"]:
            bar = Bar(f"=> `labels` for {no} analyses", max = no, suffix='%(percent)d%%'+" of "+str(no) )
        for cs in ana_coll.find(cs_query):
            if not BYC["TEST_MODE"]:
                bar.next()
            bs_id = cs.get("biosample_id", "___none___")
            bios = bios_coll.find_one({"id": bs_id})
            if not bios:
                continue
            bs_label = bios.get("label", "")
            if len(bs_label) < 2:
                bs_label = bios.get("notes", "")
            if len(bs_label) < 2:
                bs_label = bs_id

            if BYC["TEST_MODE"] is True:
                print(f'{cs["id"]} => {bs_label}')
            else:
                ana_coll.update_one({"_id": cs["_id"]}, {"$set": {"label": bs_label}})

        if not BYC["TEST_MODE"]:
            bar.finish()

    ana_coll.update_many(
        {"operation.id":"EDAM:operation_3227"},
        {"$unset":{"cnv_chro_stats": "", "cnv_stats":"", "cnv_statusmaps": ""}}
    )
    ana_coll.update_many(
        {"operation.id": "EDAM:operation_3961"},
        {"$set":{"operation.label": "Copy number variation detection"}}
    )

    for bios in bios_coll.find({"cohorts.id":"pgx:cohort-TCGA"}):
        ana_coll.update_many(
            {"biosample_id": bios["id"], "operation.id": "EDAM:operation_3961"},
            {"$set":{"platform_model": {"id":"geo:GPL6801", "label":"[GenomeWideSNP_6] Affymetrix Genome-Wide Human SNP 6.0 Array"}}}
        )

    #>------------------------------------------------------------------------<#

    if "y" in todos.get("update_cs_statusmaps", "n").lower():
        command = f'{loc_path}/analysesStatusmapsRefresher.py -d {ds_id} --limit {BYC_PARS.get("limit", 200)}'
        print(f'==> executing "{command}"')
        system(command)

    #>------------------------ / analyses ------------------------------------<#

    #>------------------------ individuals -----------------------------------<#

    # NCIT:C2919 prostate
    # male_histos = ["NCIT:C2919"]
    # female_histos = ["NCIT:C2919"]

    female_uberon = ["UBERON:0000002", "UBERON:0000995", "UBERON:0000474"]
    male_uberon = ["UBERON:0002367", "UBERON:0000473"]

    if "y" in todos.get("logical_sex_assignments", "n").lower():
        for bios in bios_coll.find({"sample_origin_detail.id":{"$in": female_uberon}}):
            if not (f_id := bios.get("individual_id")):
                continue
            ind_coll.find_one_and_update(
                {"id": f_id},
                {"$set":{"sex": { "id": 'NCIT:C16576', "label": 'female' }}}
            )

        for bios in bios_coll.find({"sample_origin_detail.id":{"$in": male_uberon}}):
            if not (m_id := bios.get("individual_id")):
                continue
            ind_coll.find_one_and_update(
                {"id": m_id},
                {"$set":{"sex": { "id": 'NCIT:C20197', "label": 'male' }}}
            )

    # age_days
    if "y" in todos.get("individual_times_days", "n").lower():
        query = {"index_disease.onset.age": {"$regex": '^P'}}
        no = ind_coll.count_documents(query)
        bar = Bar(f"=> `age_days` ...", max = no, suffix='%(percent)d%%'+" of "+str(no) )

        age_c = 0
        for ind in ind_coll.find(query):
            age_days = days_from_iso8601duration(ind["index_disease"]["onset"]["age"])
            if age_days is False:
                continue
            ind_coll.update_one({"_id": ind["_id"]}, {"$set": {"index_disease.onset.age_days": age_days}})
            age_c += 1
            bar.next()

        bar.finish()

        print(f'=> {age_c} individuals received an `index_disease.onset.age_days` value.')

        query = {"index_disease.followup_time": {"$regex": '^P'}}
        no = ind_coll.count_documents(query)
        bar = Bar(f"=> `followup_days` ...", max = no, suffix='%(percent)d%%'+" of "+str(no) )

        f_c = 0
        for ind in ind_coll.find(query):
            followup_days = days_from_iso8601duration(ind["index_disease"]["followup_time"])
            if followup_days is False:
                continue
            ind_coll.update_one(
                {"_id": ind["_id"]},
                {"$set": {"index_disease.followup_days": followup_days}}
            )
            f_c += 1
            bar.next()
        bar.finish()

        print(f'=> {f_c} individuals received an `index_disease.followup_days` value.')

    #>------------------------------------------------------------------------<#

    cancer_query = {"biosample_status.id":{"$ne":'EFO:0009654'}, "histological_diagnosis.id": {"$regex": '^NCIT:'}}
    no = bios_coll.count_documents(cancer_query)
    bar = Bar(f"=> `index_disease.disease_code` ...", max = no, suffix='%(percent)d%%'+" of "+str(no) )
    for bios in bios_coll.find(cancer_query):
        disease_code = bios.get("histological_diagnosis", None)
        if disease_code:
            ind_coll.update_one(
                {"id": bios["individual_id"]},
                {"$set": {"index_disease.disease_code": disease_code}}
            )
        bar.next()
    bar.finish()

    print(f'... now updating `individual_info` in biosamples.')

    no = ind_coll.count_documents({"index_disease":{"$exists": True}})
    bar = Bar(f"=> individuals", max = no, suffix='%(percent)d%%'+" of "+str(no) )
    for ind in ind_coll.find({"index_disease":{"$exists": True}}):
        bar.next()

        ind_info = {}
        if (fd := ind.get("index_disease", {}).get("followup_days")):
            ind_info.update({"followup_days": fd})
        if (ad := ind.get("index_disease", {}).get("onset", {}).get("age_days")):
            ind_info.update({"age_days": ad})
        if (sex := ind.get("sex")):
            if (sid := sex.get("id")):
                ind_info.update({"sex": sex})
        if len(ind_info.keys()) < 1:
            continue
        for bios in bios_coll.find({"individual_id":ind["id"], "biosample_status.id":{"$ne":'EFO:0009654'}}):
            update_obj = {"individual_info": ind_info}
            if "P" in (coll_iso := bios.get("collection_moment", "")):
                age_days = days_from_iso8601duration(coll_iso)
                if age_days is not False:
                    update_obj.update({"collection_moment_days": age_days})
                    ind_coll.update_one({"_id": ind["_id"]}, {"$set": {"index_disease.onset.age_days": age_days, "index_disease.onset.age": coll_iso}})
                    print(f'=> updated individual {ind["id"]} with collection moment age {coll_iso}')
            bios_coll.update_one({"_id": bios["_id"]}, {"$set": update_obj})
    bar.finish()

    #>----------------------- / individuals ----------------------------------<#

    #>-------------------------- variants ------------------------------------<#

    var_coll = data_db["variants"]

    # length
    if "y" in todos.get("update_variants", "n").lower():
        query = {}
        no = var_coll.estimated_document_count(query)
        bar = Bar(f"=> variants ...", max = no, suffix='%(percent)d%%'+" of "+str(no) )

        v_c = 0
        e_c = 0
        BV = ByconVariant()
        for var in var_coll.find(query):
            variant = BV.vrsVariant(var)
            if not (l := variant.get("info", {}).get("var_length")):
                e_c += 1
            v_c += 1
            var_coll.update_one({"_id": var["_id"]}, {"$set": variant})
            bar.next()

        bar.finish()

        print(f'=> {v_c} variants were updated.')
        print(f'=> {e_c} variants had no length (e.g. adjacencies...)')

    #>------------------------- / variants -----------------------------------<#

    #>---------------------- update collations -------------------------------<#

    if "y" in todos.get("update_collations", "n").lower():
        command = f'{loc_path}/collationsCreator.py -d {ds_id} --limit {BYC_PARS.get("limit", 200)}'
        print(f'\n{__hl()}==> executing \n\n{command}\n')
        system(command)

    #>--------------------- / update collations ------------------------------<#

    #>--------------------- update frequencymaps -----------------------------<#

    if "y" in todos.get("update_frequencymaps", "n").lower():
        command = f'{loc_path}/collationsFrequencymapsCreator.py -d {ds_id} --limit {BYC_PARS.get("limit", 200)}'
        if (mode := BYC_PARS.get("mode")):
           command += f' --mode {mode}'
        print(f'\n{__hl()}==> executing "{command}"\n')
        system(command)

    #>-------------------- / update frequencymaps ----------------------------<#

    #>---------------------- info db update ----------------------------------<#

    if "y" in todos.get("datasets_counts", "n").lower():
        ByconInfo().update_beaconinfo()

    #>--------------------- / info db update ---------------------------------<#


################################################################################
#################################### subs ######################################
################################################################################


def __hl():
    return "".join(["#"] * 80) + "\n"

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
