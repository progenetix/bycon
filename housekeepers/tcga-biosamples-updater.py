#!/usr/local/bin/python3

from datetime import datetime
from os import path, pardir
from pymongo import MongoClient

from bycon import *
from byconServiceLibs import assert_single_dataset_or_exit, ByconTSVreader

################################################################################

tcga_file = BYC_PARS.get("inputfile")
print(f'... processing {tcga_file}')

data, fields = ByconTSVreader().fileToDictlist(tcga_file)

mongo_client = MongoClient(host=BYC_DBS["mongodb_host"])["progenetix"]
bios_coll = mongo_client["biosamples"]
ana_coll = mongo_client["analyses"]
ind_coll = mongo_client["individuals"]

not_found = 0
ana_found = 0
ind_found = 0

for bios in data:
	bios_id = bios.get("biosample_id")
	ana_found += ana_coll.count_documents({"biosample_id": bios_id})
	ind_found += ind_coll.count_documents({"id": bios.get("individual_id")})
	if not (ext_bios := bios_coll.find_one({"id": bios_id})):
		print(f"!!! {bios_id} wasn't found in biosamples !!!")
		not_found += 1
		continue
	ext_bios__id = ext_bios.get("_id")

	update_obj = {
		"references": {
			"tcgaproject": {"id": bios.get("tcgaproject_id"), "label": bios.get("tcgaproject_label")},
		},
		"cohorts": ext_bios.get("cohorts", [])
	}

	if not (bss_id := bios.get("biosample_status_id")):
		print(f"!!! {bios_id} doesn't have a `biosample_status_id`!!!")
		continue

	update_obj["cohorts"].append({"id":"pgx:cohorts-TCGA", "label": "TCGA samples"})
	if "EFO:0009656" in bss_id:
		update_obj["cohorts"].append({"id":"pgx:cohorts-TCGAcancers", "label": "TCGA cancer samples"})
	else:
		update_obj["cohorts"].append({"id":"pgx:cohorts-TCGAreferences", "label": "TCGA reference samples"})


	prjsonnice(bios_id)
	prjsonnice(update_obj)
	# bios_coll.update_one( { "_id": ext_bios__id }, { '$set': update_obj }  )


print(not_found)
print(f"...{ana_found} analyses have been found")
print(f"...{ind_found} biosamples had an individual assigned")
