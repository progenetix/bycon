#!/usr/bin/env python3

import re, json, yaml, sys, datetime
from isodate import date_isoformat
from os import path, environ, pardir, system
from pymongo import MongoClient
from progress.bar import Bar

from bycon import *
from byconServiceLibs import *

loc_path = path.dirname( path.abspath(__file__) )
lib_path = path.join(loc_path , "lib")
sys.path.append( lib_path )
from mongodb_utils import mongodb_update_indexes
from doc_generator import doc_generator

services_conf_path = path.join( loc_path, "config" )

################################################################################
################################################################################
################################################################################

def main():
    initialize_bycon_service()
    read_service_prefs("housekeeping", services_conf_path)

    set_collation_types()

    # TODO: rewrap, use config etc.
    generated_docs_path = path.join( loc_path, pardir, "docs", "generated")
    bycon_generated_docs_path = path.join( loc_path, pardir, pardir, "bycon", "docs", "generated")
    doc_generator(generated_docs_path)
    doc_generator(bycon_generated_docs_path)

    ds_id = assertSingleDatasetOrExit()

    # collecting the actions
    todos = {
        "mongodb_index_creation": input("Check & refresh MongoDB indexes?\n(y|N): "),
        "individual_age_days": input("Recalculate `age_days` in individuals?\n(y|N): "),
        "analyses_labels": input("Create/update `label` field for analyses, from biosamples?\n(y|N): "),
        "variant_lengths": input("Recalculate `info.var_length` in variants?\n(y|N): "),
        "update_cs_statusmaps": input(f'Update statusmaps in `analyses` for {ds_id}?\n(y|N): '),
        "update_collations": input(f'Create `collations` for {ds_id}?\n(Y|n): '),
        "update_frequencymaps": input(f'Create `frequencymaps` for {ds_id} collations?\n(Y|n): '),
        "datasets_counts": input("Recalculate counts for all datasets?\n(y|N): ")
    }

    data_db = MongoClient(host=DB_MONGOHOST)[ ds_id ]

    #>-------------------- MongoDB index updates -----------------------------<#

    if "y" in todos.get("mongodb_index_creation", "n").lower():
        print(f'\n{__hl()}==> updating indexes for {ds_id}"')
        mongodb_update_indexes(ds_id)

    #>------------------- / MongoDB index updates ----------------------------<#

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

    if "y" in todos.get("update_cs_statusmaps", "y").lower():
        print(f'==> executing "{loc_path}/analysesStatusmapsRefresher.py -d {ds_id} --limit {BYC_PARS.get("limit", 200)}"')
        system(f'{loc_path}/analysesStatusmapsRefresher.py -d {ds_id}')

    #>------------------------ / analyses ------------------------------------<#

    #>------------------------ individuals -----------------------------------<#

    ind_coll = data_db["individuals"]

    # age_days
    if "y" in todos.get("individual_age_days", "n").lower():
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

    #>----------------------- / individuals ----------------------------------<#

    #>-------------------------- variants ------------------------------------<#

    ind_coll = data_db["variants"]
    update_field = "info.var_length"

    # length
    if "y" in todos.get("variant_lengths", "n").lower():
        # query = {"location.start": {"$exists": True}, "location.end": {"$exists": True}}
        # no = ind_coll.count_documents(query)
        query = {}
        no = ind_coll.estimated_document_count(query)
        bar = Bar(f"=> `{update_field}` ...", max = no, suffix='%(percent)d%%'+" of "+str(no) )

        v_c = 0
        e_c = 0
        for ind in ind_coll.find(query):
            loc = ind.get("location", {})
            s = loc.get("start")
            e = loc.get("end")
            if not s or not e:
                e_c += 1
                continue
            ind_coll.update_one({"_id": ind["_id"]}, {"$set": {update_field: e - s}})
            v_c += 1
            bar.next()

        bar.finish()

        print(f'=> {v_c} variants with updated `{update_field}` value.')
        print(f'=> {e_c} variants failed to update...')

    #>------------------------- / variants -----------------------------------<#

    #>---------------------- info db update ----------------------------------<#

    if "y" in todos.get("datasets_counts", "n").lower():

        print(f'\n{__hl()}==> Updating dataset statistics in "{HOUSEKEEPING_DB}.{HOUSEKEEPING_INFO_COLL}"')

        b_info = __dataset_update_counts()

        info_coll = MongoClient(host=DB_MONGOHOST)[ HOUSEKEEPING_DB ][ HOUSEKEEPING_INFO_COLL ]
        info_coll.delete_many( { "date": b_info["date"] } ) #, upsert=True
        info_coll.insert_one( b_info ) #, upsert=True 

        print(f'\n{__hl()}==> updated entry {b_info["date"]} in {HOUSEKEEPING_DB}.{HOUSEKEEPING_INFO_COLL}')

    #>--------------------- / info db update ---------------------------------<#

    #>---------------------- update collations -------------------------------<#

    if not "n" in todos.get("update_collations", "y").lower():
        print(f'\n{__hl()}==> executing "{loc_path}/collationsCreator.py -d {ds_id} --limit {BYC_PARS.get("limit", 200)}"\n')
        system(f'{loc_path}/collationsCreator.py -d {ds_id}')

    #>--------------------- / update collations ------------------------------<#

    #>--------------------- update frequencymaps -----------------------------<#

    if not "n" in todos.get("update_frequencymaps", "y").lower():
        print(f'\n{__hl()}==> executing "{loc_path}/frequencymapsCreator.py -d {ds_id} --limit {BYC_PARS.get("limit", 200)}"\n')
        system(f'{loc_path}/frequencymapsCreator.py -d {ds_id}')

    #>-------------------- / update frequencymaps ----------------------------<#

################################################################################
#################################### subs ######################################
################################################################################

def __dataset_update_counts():

    b_info = { "date": date_isoformat(datetime.datetime.now()), "datasets": { } }
    mongo_client = MongoClient(host=DB_MONGOHOST)

    # this is independend of the dataset selected for the script & will update
    # for all in any run
    for i_ds_id in BYC["dataset_definitions"].keys():
        if not i_ds_id in BYC["DATABASE_NAMES"]:
            print(f'¡¡¡ Dataset "{i_ds_id}" does not exist !!!')
            continue

        ds_db = mongo_client[ i_ds_id ]
        b_i_ds = { "counts": { }, "updated": datetime.datetime.now().isoformat() }
        c_n = ds_db.list_collection_names()
        for c in ["biosamples", "individuals", "variants", "analyses"]:
            if c not in c_n:
                continue

            no = ds_db[ c ].estimated_document_count()
            b_i_ds["counts"].update( { c: no } )
            if c == "variants":
                v_d = { }
                bar = Bar(i_ds_id+' variants', max = no, suffix='%(percent)d%%'+" of "+str(no) )
                for v in ds_db[ c ].find({ "variant_internal_id": {"$exists": True }}):
                    v_d[ v["variant_internal_id"] ] = 1
                    bar.next()
                bar.finish()
                b_i_ds["counts"].update( { "variants_distinct": len(v_d.keys()) } )

        b_info["datasets"].update({i_ds_id: b_i_ds})
    
    return b_info

################################################################################

def __hl():
    return "".join(["#"] * 80) + "\n"

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
