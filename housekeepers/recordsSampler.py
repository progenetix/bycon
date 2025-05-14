#!/usr/local/bin/python3

from os import pardir, path, system
from bycon import *
from pymongo import MongoClient
from random import sample as random_samples

from bycon import byconServiceLibs, ByconDatasets
from bycon_importer import ByconImporter
from service_helpers import assert_single_dataset_or_exit

loc_path = path.dirname( path.abspath(__file__) )
project_path = path.join(loc_path , pardir)
rsrc_path = path.join(project_path, "rsrc")

"""
The `recordsSampler.py` script is used to create the example database
`examplez` from an existing data set. It uses a standard Beacon query (with
the `bycon` specific extensions such as global OR option for filters) and the
`--limit` parameter to create a small, manageable data set from the corresponding
number of random records pulled from the query results. Alternatively one can
provide a default set of test queries through a `local/test_queries.yaml` file
structured like this example:

```
CDKN2AcnvQuery:
  filters:
    - NCIT:C3058
  reference_name: refseq:NC_000009.12
  start: [21000001,21975098]
  end: [21967753,23000000]
  variant_type: EFO:0030067

EIF4A1snvQuery:
  reference_name: refseq:NC_000017.11
  start: [7577120]
  variant_type: SO:0001059
  alternate_bases: A
  reference_bases: G
```

The script will first create the database and then populate it with the records
for the standard entities. Optionally one can select to proceed with the additional
steps for a CNV supporting database and create an archive for distribution.

#### Examples

* `.recordsSampler.py -d progenetix --output examplez --filters "pgx:icdom-81703,pgx:icdom-94003" --filterLogic OR  --limit 222`
* `.recordsSampler.py -d progenetix --output examplez --mode testqueries`
"""

ds_id = assert_single_dataset_or_exit()
database_names = ByconDatasets().get_database_names()
examples_db = BYC_PARS.get("output", "examplez")
proceed = input(f'Re-create the example "{examples_db}" database from {ds_id} data? (y/N): ')
if not "y" in proceed.lower():
    print("Exiting...")
    exit()
if examples_db in database_names and not "examplez" in examples_db:
    proceed = input(f'¡ This will delete the existing "{examples_db}" database !\nPlease type the database name to confirm: ')
    if examples_db != proceed:
        print("Exiting...")
        exit()

BYC_PARS.update({"response_entity_path_id":"individuals"})
BYC_PARS.update({"inputfile":"___dummy___"})
BYC_PARS.update({"output": examples_db})
ByconEntities().set_entities()

# TODO: prototyping use of a seies of queries to collect matching
# individuals & subsampling those. 
a_i_ids = MultiQueryResponses(ds_id).get_individual_ids()
proceed = input(f'Proceed importing {len(a_i_ids)} and depending records? (y/N): ')
if not "y" in proceed.lower():
    exit()

BYC_PARS.update({"individual_ids": list(a_i_ids)})    
BRS = ByconResultSets()
ds_results = BRS.datasetsResults()
if not (ds := ds_results.get(ds_id)):
    print(f"No results for queries against '{ds_id}':")
    print(f'{"\n".join(BYC.get("NOTES", []))}')
    exit()

mongo_client = MongoClient(host=DB_MONGOHOST)
mongo_db = mongo_client[examples_db]
test_colls = mongo_db.list_collection_names()
for coll in list(test_colls):
    if not BYC["TEST_MODE"]:
        mongo_db[coll].drop()

mongo_db = mongo_client[examples_db]
for coll in list(test_colls):
    if not BYC["TEST_MODE"]:
        mongo_db.create_collection(coll)

ByconImporter(False).move_individuals_and_downstream_from_ds_results(ds_results)

print(f"Finished re-creating the example database '{examples_db}'.")
print(f"For full functionality you might want to run \n\n`{loc_path}/housekeeping.py -d {examples_db}`\n\nor continue with the following commands.\n")

proceed = input(f'Proceed with running the (time consuming) aggregation functions? (y/N): ')
if not "y" in proceed.lower():
    exit()

print(f'\n==> updating indexes for {examples_db}"')
system(f'{loc_path}/mongodbIndexer.py -d {examples_db}')

cmd = f'{loc_path}/collationsCreator.py -d {examples_db} --limit 0'
print(f'\n==> executing\n\n{cmd}\n')
system(cmd)

cmd = f'{loc_path}/collationsFrequencymapsCreator.py -d {examples_db} --limit 0'
print(f'\n==> executing\n\n{cmd}\n')
system(cmd)

for db in (examples_db, "_byconServicesDB"):
    mongo_dir = Path( path.join( rsrc_path, "mongodump" ) )
    e_ds_dir = Path( path.join( mongo_dir, db ) )
    e_ds_archive = f'{db}.tar.gz'
    system(f'rm -rf {db}')
    system(f'mongodump --db {db} --out {mongo_dir}')
    system(f'cd {mongo_dir} && tar -czf {e_ds_archive} {db} && rm -rf {db}')
    
    print(f'Created {db} archive "{e_ds_archive}"')
