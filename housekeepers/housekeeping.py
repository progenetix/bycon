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
        "variant_lengths": input("Recalculate `info.var_length` in variants?\n(y|N): "),
        "update_cs_statusmaps": input(f'Update statusmaps in `analyses` for {ds_id}?\n(y|N): '),
        "update_collations": input(f'Create `collations` for {ds_id}?\n(Y|n): '),
        "update_frequencymaps": input(f'Create `frequencymaps` for {ds_id} collations?\n(Y|n): '),
        "datasets_counts": input("Recalculate counts for all datasets?\n(y|N): "),
        "geolocs_updates": input("Relabel all biosamples with existing geolocation?\n(y|N): ")
    }

    data_db = MongoClient(host=BYC_DBS["mongodb_host"])[ ds_id ]
    services_db = MongoClient(host=BYC_DBS["mongodb_host"])[BYC_DBS["services_db"]]

    #>-------------------- MongoDB index updates -----------------------------<#

    if "y" in todos.get("mongodb_index_creation", "n").lower():
        print(f'\n{__hl()}==> updating indexes for {ds_id}"')
        system(f'{loc_path}/mongodbIndexer.py -d {ds_id}')

    #>------------------- / MongoDB index updates ----------------------------<#

    #>------------------------- biosamples -----------------------------------<#

    #>------------------------ geo locations ---------------------------------<#

    if "y" in todos.get("geolocs_updates", "n").lower():
        geo_coll = services_db[BYC_DBS["geolocs_coll"]]
        biosamples_coll = data_db[BYC_DBS["biosample_coll"]]
        atlantis = {
                "geonameid": "0",
                "id": "atlantis::bermudatriangle",
                "geo_source": "custom entry",
                "geo_location": {
                    "type": 'Feature',
                    "geometry": { "type": 'Point', "coordinates": [ -71, 25 ] },
                    "properties": {
                        "geoprov_id": "atlantis::bermudatriangle::-71::25",
                        "label": f"Atlantis, Bermuda Triangle",
                        "ISO3166alpha2": "00",
                        "ISO3166alpha3": "000",
                        "city": "Atlantis",
                        "continent": "AT",
                        "country": "Bermuda Triangle"
                }
              }
            }

        gn = biosamples_coll.count_documents({})
        atl_count = 0
        if not BYC["TEST_MODE"]:
            bar = Bar(f"=> {gn} samples for geolocs", max = gn, suffix='%(percent)d%%'+" of "+str(gn) )

        for s in biosamples_coll.find():
            if not BYC["TEST_MODE"]:
                bar.next()
            bgl = s.get("geo_location")
            if type(bgl) is not dict:
                atl_count += 1
                nearest = [atlantis]
            else:
                pcoords = bgl.get("geometry", {}).get("coordinates", [])
                if not pcoords or len(pcoords) != 2:
                    nocoords += 1
                    print(bgl.get("properties"))
                    continue
                geo_q = {
                    "geo_location.geometry": {
                        "$near": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": pcoords
                            },
                            "$maxDistance": 500000
                        }
                    }
                }
                nearest = list(geo_coll.find(geo_q).limit(1))

            if len(nearest) < 1:
                continue

            if not (n_g_l := nearest[0].get("geo_location")):
                continue

            if not BYC["TEST_MODE"]:
                biosamples_coll.update_one(
                    {"_id": s.get("_id")},
                    {"$set": {"geo_location": n_g_l}}
                )
            else:
                print(f"Would update sample {bgl} to geo_location {n_g_l}")

        if not BYC["TEST_MODE"]:
            bar.finish()
        
        print(f"Samples without valid geo_location: {atl_count}")


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

    ind_coll = data_db["individuals"]

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
            ind_coll.update_one({"_id": ind["_id"]}, {"$set": {"index_disease.followup_days": followup_days}})
            f_c += 1
            bar.next()

        bar.finish()

        print(f'=> {f_c} individuals received an `index_disease.followup_days` value.')

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
