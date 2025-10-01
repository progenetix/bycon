#!/usr/local/bin/python3

from datetime import datetime
from os import path, pardir
from pymongo import MongoClient

# from vrs_translator import AlleleTranslator
from ga4gh.vrs.dataproxy import create_dataproxy

from bycon import *
from byconServiceLibs import assert_single_dataset_or_exit, ByconTSVreader, ByconDatatableExporter

# ./housekeepers/_dipg-updater.py -d progenetix --filters "pgx:cohort-DIPG" --requestEntityPathId individuals --debugMode 0

seqrepo_rest_service_url = 'seqrepo+file:///Users/Shared/seqrepo/2024-12-20'
seqrepo_dataproxy = create_dataproxy(uri=seqrepo_rest_service_url)
vrs_allele_translator = AlleleTranslator(data_proxy=seqrepo_dataproxy)

assert_single_dataset_or_exit()

################################################################################

MAF_file = BYC_PARS.get("inputfile")
print(f'... processing {MAF_file}')

data, fields = ByconTSVreader().file_to_dictlist(MAF_file)

data_ids = set()
for l in data:
	data_ids.add(l.get("Tumor_Sample_Barcode"))
data_ids = list(data_ids)
print(f'... {len(data_ids)} ids exist in the data file')

################################################################################

ds_id = ByconDatasets().get_dataset_ids()[0]
dsr = ByconResultSets().datasetsResults()

ind_ids = dsr[ds_id]['individuals.id']["target_values"]

mongo_client = MongoClient(host=DB_MONGOHOST)[ds_id]
ind_coll = mongo_client["individuals"]
bs_coll = mongo_client["biosamples"]
ana_coll = mongo_client["analyses"]
var_coll = mongo_client["variants"]

ids = {
	"individuals": {},
	"biosamples": set(),
	"analyses": set(),
	"analyses_with_alleles": set()
}

for ind_id in ind_ids:
	ind = ind_coll.find_one({"id": ind_id})
	l_ids = ind.get("info", {}).get("legacy_ids", [])
	l_ids = [x for x in l_ids if "DIPG_IND" in x]
	if len(l_ids) != 1:
		continue
	phggid = re.sub("DIPG_IND_", "pHGG_META_", l_ids[0])
	if phggid not in data_ids:
		continue
	ids["individuals"].update({phggid: ind_id})

	bios = bs_coll.find({"individual_id": ind_id, "histological_diagnosis.id": {"$ne": "NCIT:C132256"}})
	# bs_ids = bs_coll.distinct("id", {"individual_id": ind_id, "histological_diagnosis.id": "NCIT:C4822"})
	bs = list(bios)[-1]
	bs_id = bs.get("id")
	print(f'histo: {bs["histological_diagnosis"]}')
	# print(f'{phggid}: {bs_id}')
	ids["biosamples"].add(bs_id)
	anas = list(ana_coll.find({"biosample_id": bs_id}))
	if len(anas) < 1:
		continue
	for ana in anas:
		ana_id = ana.get("id")
		ids["analyses"].add(ana_id)
		print(f'{ana_id}: {ana.get("operation", {}).get("id", "****")}')
		v_types = var_coll.distinct("type", {"analysis_id": ana_id})
		# print(f'{phggid}: {bs_id} - {ana_id}: {v_types}')
		if "Allele" in v_types:
			ids["analyses_with_alleles"].add(ana_id)
		for avid in var_coll.distinct("_id", {"analysis_id": ana_id, "type": "Allele"}):
			# av = var_coll.find_one({"_id": avid})
			# print(f'...... would delete {avid} - {av.get("type")}')
			var_coll.delete_one({"_id": avid})

for k, v in ids.items():
	print(f'{k}: {len(v)}')
# exit()
import_ids = ids["individuals"].keys()
import_variants = []

for v in data:
	if not (legacy_id := l.get("Tumor_Sample_Barcode", "___none___")) in import_ids:
		continue

	ref = v.get("Reference_Allele")
	# ref = ''.join(["N" for char in ref])

	gnomad_string = f'{v.get("Chromosome")}-{v.get("Start_Position")}-{ref}-{v.get("Tumor_Seq_Allele")}'

	vrs_v = vrs_allele_translator.translate_from(gnomad_string, "gnomad", require_validation=False)
	vrs_v = decamelize(vrs_v.model_dump(exclude_none=True))


	i_v = {
		"info": {
			"individual_legacy_id": legacy_id

		},
		"individual_id": ids["individuals"].get(legacy_id),
		"gnomad_string": f'{v.get("Chromosome")}-{v.get("Start_Position")}-{v.get("Reference_Allele")}-{v.get("Tumor_Seq_Allele")}',
		"vrs_allele": vrs_v
	}

	import_variants.append(i_v)

prjsonnice(import_variants)

print(f'... {len(data)} lines were read in')
print(f'... {len(ids["analyses_with_alleles"])} analyses were labeled as "Allele" before')
print(f'... {len(import_ids)} match existing legacy ids')
print(f'==>> {len(import_variants)} were converted')











