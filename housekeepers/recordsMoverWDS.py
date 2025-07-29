#!/usr/local/bin/python3

import sys
from os import pardir, path
# from bycon import *

from bycon import (
    BYC,
    BYC_PARS,
    ByconID,
    ByconEntities,
    ByconResultSets,
    prdbug
)
from byconServiceLibs import assert_single_dataset_or_exit, ByconDatatableExporter, ByconImporter

# loc_path = path.dirname( path.abspath(__file__) )
# lib_path = path.join(loc_path , pardir, "importers", "lib")
# sys.path.append( lib_path )
# from bycon_importer import ByconImporter

"""
The `recordsMoverWDS.py` script is used to move records from a source database
(indicated with `-d`) to a target database (indicated with `--output`). It requires
the use of a tab-separated file with the record `individual_id` identifiers to be moved.

* ./housekeepers/recordsMoverWDS.py -d progenetix --output cellz -i ./imports/1kdeltest.tsv --testMode false
"""
# BYC_PARS.update({"request_entity_path_id": "individuals"})
BYC.update({"BYC_DATASET_IDS": BYC_PARS.get("dataset_ids", [])})
ByconEntities().set_entities()
assert_single_dataset_or_exit()

#TODO: Here only as prototype for a query based sample selection
if len(BYC_PARS.get("filters", [])) > 0:
    f_d = ByconResultSets().get_flattened_data()
    file = path.join(*BYC["env_paths"]["server_tmp_dir_loc"], f"individuals-{ByconID(0).makeID()}.tsv")
    BYC_PARS.update({"outputfile": file, "inputfile": file})
    ByconDatatableExporter(f_d).export_datatable()    

BI = ByconImporter()
BI.move_records_and_downstream("individual")
