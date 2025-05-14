#!/usr/local/bin/python3

from bycon import *
from pymongo import MongoClient

from bycon import byconServiceLibs
from service_helpers import assert_single_dataset_or_exit


"""
* ./housekeepers/queriesTester.py -d progenetix --filters "pgx:icdom-81703"
* ./housekeepers/queriesTester.py -d progenetix --mode testqueries
"""

################################################################################
################################################################################
################################################################################

ds_id = assert_single_dataset_or_exit()
target_path_id = "individuals"
ho_key = f'{target_path_id}.id'
BYC_PARS.update({"response_entity_path_id":target_path_id})
ByconEntities().set_entities()

r_ids = MultiQueryResponses(ds_id).get_individual_ids()

print(f'{"\n".join(BYC.get("NOTES", []))}')


