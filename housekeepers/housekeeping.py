#!/usr/local/bin/python3

import re, json, yaml, sys
from datetime import datetime
from isodate import date_isoformat
from os import path, environ, pardir, system
from pymongo import MongoClient
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
        "individual_times_days": input("Recalculate `age_days` and `followup_days` in individuals?\n(y|N): "),
        "analyses_labels": input("Create/update `label` field for analyses, from biosamples?\n(y|N): "),
        "update_variants": input("Update variants to latest format (VRS v2)?\n(y|N): "),
        "update_cs_statusmaps": input(f'Update statusmaps in `analyses` for {ds_id}?\n(y|N): '),
        "update_collations": input(f'Create `collations` for {ds_id}?\n(Y|n): '),
        "update_frequencymaps": input(f'Create `frequencymaps` for {ds_id} collations?\n(Y|n): '),
        "datasets_counts": input("Recalculate counts for all datasets?\n(y|N): "),
        "geolocs_updates": input("Relabel all biosamples with existing geolocation?\n(y|N): ")
    }

    data_db = MongoClient(host=BYC_DBS["mongodb_host"])[ds_id]
    services_db = MongoClient(host=BYC_DBS["mongodb_host"])[BYC_DBS["services_db"]]

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
        analyses_coll = data_db["analyses"]
        bios_coll = data_db["biosamples"]
        no = analyses_coll.count_documents(cs_query)

        if not BYC["TEST_MODE"]:
            bar = Bar(f"=> `labels` for {no} analyses", max = no, suffix='%(percent)d%%'+" of "+str(no) )
        for cs in analyses_coll.find(cs_query):
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
                analyses_coll.update_one({"_id": cs["_id"]}, {"$set": {"label": bs_label}})

        if not BYC["TEST_MODE"]:
            bar.finish()

    #>------------------------------------------------------------------------<#

    if "y" in todos.get("update_cs_statusmaps", "n").lower():
        command = f'{loc_path}/analysesStatusmapsRefresher.py -d {ds_id} --limit {BYC_PARS.get("limit", 200)}'
        print(f'==> executing "{command}"')
        system(command)

    #>------------------------ / analyses ------------------------------------<#

    #>------------------------ individuals -----------------------------------<#

    ind_coll = data_db[BYC_DBS["individual_coll"]]
    bios_coll = data_db[BYC_DBS["biosample_coll"]]

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
            for bios in bios_coll.find({"individual_id":ind["id"], "biosample_status.id":{"$ne":'EFO:0009654'}}):
                if (ind_info := bios.get("individual_info")) is not True:
                    ind_info = {}
                ind_info.update({"age_at_diagnosis_days": age_days})
                bios_coll.update_one({"_id": bios["_id"]}, {"$set": {"individual_info": ind_info}})
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
            for bios in bios_coll.find({"individual_id":ind["id"], "biosample_status.id":{"$ne":'EFO:0009654'}}):
                if (ind_info := bios.get("individual_info")) is not True:
                    ind_info = {}
                ind_info.update({"index_disease_followup_days": followup_days})
                bios_coll.update_one({"_id": bios["_id"]}, {"$set": {"individual_info": ind_info}})
            bar.next()

        bar.finish()

        print(f'=> {f_c} individuals received an `index_disease.followup_days` value.')

        print(f'... now updating `individual_info.index_disease` in biosamples.')

        for ind in ind_coll.find({"index_disease":{"$exists": True}}):
            for bios in bios_coll.find({"individual_id":ind["id"], "biosample_status.id":{"$ne":'EFO:0009654'}}):
                bios_coll.update_one({"_id": bios["_id"]}, {"$set": {"individual_info": {"index_disease": ind.get("index_disease", {})}}})

        for ind in ind_coll.find({"sex":{"$exists": True}}):
            for bios in bios_coll.find({"individual_id":ind["id"]}):
                bios_coll.update_one({"_id": bios["_id"]}, {"$set": {"individual_info": {"sex": ind.get("sex", {})}}})

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
