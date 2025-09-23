#!/usr/local/bin/python3

from datetime import datetime
from os import path, pardir
from pymongo import MongoClient

from bycon import *
from byconServiceLibs import assert_single_dataset_or_exit, ByconDatatableExporter, ByconDatatableExporter


ds_id = "progenetix"

BYC_PARS.update({"dataset_ids": [ds_id], "filters": [{"id":"pgx:cohort-DIPG"}]})
assert_single_dataset_or_exit()

dsr = ByconResultSets().datasetsResults()

ind_ids = dsr[ds_id]['individuals.id']["target_values"]

mongo_client = MongoClient(host=DB_MONGOHOST)[ ds_id ]
ind_coll = mongo_client["individuals"]
bs_coll = mongo_client["biosamples"]
ana_coll = mongo_client["analyses"]

for ind_id in ind_ids:
	ind = ind_coll.find_one({"id": ind_id})
	l_ids = ind.get("info", {}).get("legacy_ids", [])
	l_ids = [x for x in l_ids if "DIPG_IND" in x]
	if len(l_ids) != 1:
		continue
	phggid = re.sub("DIPG_IND_", "pHGG_META_", l_ids[0])

	bs_ids = bs_coll.distinct("id", {"individual_id": ind_id})
	ana_ids = ana_coll.distinct("id", {"individual_id": ind_id})
	print(f'{phggid}: {bs_ids} - {ana_ids}')