#!/usr/local/bin/python3

from datetime import datetime
from os import path, pardir

from bycon import byconServiceLibs, ByconVariant, prjsonnice
from bycon_importer import ByconImporter
from byconServiceLibs import import_datatable_dict_line

BI = ByconImporter()
BV = ByconVariant()
BI.get_input_file()
variants, fieldnames = BI.read_records("genomicVariant")
i = 0
for v in variants:
	i += 1
	prjsonnice(v)
	f_v = import_datatable_dict_line({"updated": datetime.now().isoformat()}, fieldnames, v, "genomicVariant")
	prjsonnice(f_v)
	vrs_v = BV.vrsVariant(f_v)
	print('\n################ VRSified #########')
	prjsonnice(vrs_v)
	print('\n############### / VRSified ########')
	if BYC["TEST_MODE"] and i > BYC_PARS.get("test_mode_count"):
		break
