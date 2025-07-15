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
        "individual_age_days": input("Recalculate `age_days` in individuals?\n(y|N): "),
        "analyses_labels": input("Create/update `label` field for analyses, from biosamples?\n(y|N): "),
        "variant_lengths": input("Recalculate `info.var_length` in variants?\n(y|N): "),
        "update_cs_statusmaps": input(f'Update statusmaps in `analyses` for {ds_id}?\n(y|N): '),
        "update_collations": input(f'Create `collations` for {ds_id}?\n(Y|n): '),
        "update_frequencymaps": input(f'Create `frequencymaps` for {ds_id} collations?\n(Y|n): '),
        "datasets_counts": input("Recalculate counts for all datasets?\n(y|N): "),
        "geolocs_updates": input("Relabel all biosamples with existing geolocation?\n(y|N): ")
    }

    data_db = MongoClient(host=DB_MONGOHOST)[ ds_id ]

    #>-------------------- MongoDB index updates -----------------------------<#

    if "y" in todos.get("mongodb_index_creation", "n").lower():
        print(f'\n{__hl()}==> updating indexes for {ds_id}"')
        system(f'{loc_path}/mongodbIndexer.py -d {ds_id}')

    #>------------------- / MongoDB index updates ----------------------------<#

    #>------------------------- biosamples -----------------------------------<#

    if "y" in todos.get("geolocs_updates", "n").lower():
        geo_db = MongoClient(host=DB_MONGOHOST)[SERVICES_DB]
        max_dist_m = 2
        biosamples_coll = data_db["biosamples"]
        dist_locs = biosamples_coll.distinct("geo_location")
        print(f'=> Found {len(dist_locs)} distinct geolocations in biosamples.')

        gn = len(dist_locs)
        if not BYC["TEST_MODE"]:
            bar = Bar(f"=> {gn} geolocations", max = gn, suffix='%(percent)d%%'+" of "+str(gn) )

        for loc in dist_locs:
            if not BYC["TEST_MODE"]:
                bar.next()
            if not isinstance(loc, dict):
                continue
            if not len(coords := loc.get("geometry", {}).get("coordinates", [])) == 2:
                continue

            city = loc.get("properties", {}).get("city", "")
            country = loc.get("properties", {}).get("country", "")

            query = { "geo_location.geometry":{
                '$near': SON(
                    [
                        (
                            '$geometry', SON(
                                [
                                    ('type', 'Point'),
                                    ('coordinates', coords)
                                ]
                            )
                        ),
                        ('$maxDistance', max_dist_m)
                    ]
                )
            }}

            if city == "Leipzig" and country == "Germany":
                loc_query = {"id": "leipzig::germany"}
            elif city == "Berlin" and country == "Germany":
                loc_query = {"id": "berlin::germany"}
            elif city == "Barcelona" and country == "Spain":
                loc_query = {"id": "barcelona::spain"}
            elif city == "Rotterdam":
                loc_query = {"id": "rotterdam::netherlands"}
            elif city == "Bochum":
                loc_query = {"id": "bochum::germany"}
            elif city == "Bologna":
                loc_query = {"id": "bologna::italy"}
            elif city == "Marseille":
                loc_query = {"id": "marseille::france"}
            elif city == "Madrid" and country == "Spain":
                loc_query = {"id": "madrid::spain"}
            elif city == "Kanazawa":
                loc_query = {"id": "kanazawashi::japan"}
            elif city == "London" and country == "United Kingdom":
                loc_query = {"id": "london::unitedkingdom"}
            elif city == "Amsterdam" and country == "Netherlands":
                loc_query = {"id": "amsterdam::netherlands"}
            elif city == "Goettingen":
                loc_query = {"id": "goettingen::germany"}
            elif city == "Bethesda":
                loc_query = {"id": "bethesda::unitedstates"}
            elif city == "Cambridge UK":
                loc_query = {"id": "cambridge::unitedkingdom"}
            elif city == "Hong Kong":
                loc_query = {"id": "hongkong::china"}
            elif city == "Leiden":
                loc_query = {"id": "leiden::netherlands"}
            elif city == "New Taipei":
                loc_query = {"id": "taipei::taiwan"}
            elif city == "Nijmegen":
                loc_query = {"id": "nijmegen::netherlands"}
            elif city == "Marburg":
                loc_query = {"id": "marburganderlahn::germany"}
            elif city == "bronx":
                loc_query = {"id": "newyorkcity::unitedstates"}
            elif city == "Plzen":
                loc_query = {"id": "pilsen::czechrepublic"}
            elif city == "saint louis":
                loc_query = {"id": "stlouis::unitedstates"}
            elif city == "Birmingham" and country == "United States of America":
                loc_query = {"id": "birmingham::unitedstates"}
            elif city == "Augusta" and country == "United States of America":
                loc_query = {"id": "augusta::unitedstates"}
            # elif city == "":
            #     loc_query = {"id": ""}
            # elif city == "" and country == "":
            #     loc_query = {"id": ""}
            else:
                loc_query = query

            geolocs = mongo_result_list(SERVICES_DB, GEOLOCS_COLL, loc_query, { '_id': False } )
            if len(geolocs) != 1:
                e = [city, country, coords[0], coords[1], len(geolocs)]
                print("\t".join(str(x) for x in e))

                continue

            # continue

            geo_location = geolocs[0].get("geo_location", {})
            geo_location["properties"].update({"geoprov_id": geolocs[0].get("id", "")})

            dist_k = "_id"
            loc_samples = biosamples_coll.distinct(dist_k, query)
            if BYC["TEST_MODE"]:
                prjsonnice(geo_location)
                print(f'=> Found {len(loc_samples)} biosamples for {city}, {country}\n')

            for bio_s_id in loc_samples:
                if BYC["TEST_MODE"]:
                    print(f'==> Updating biosample {bio_s_id} with geolocation {geo_location}')
                else:
                    biosamples_coll.update_one(
                        {dist_k: bio_s_id},
                        {"$set": {"geo_location": geo_location}}
                    )

        if not BYC["TEST_MODE"]:
            bar.finish()


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
