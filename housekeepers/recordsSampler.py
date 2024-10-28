#!/usr/bin/env python3

from os import pardir, path, system
from bycon import *
from pymongo import MongoClient

loc_path = path.dirname( path.abspath(__file__) )
project_path = path.join(loc_path , pardir)
rsrc_path = path.join(project_path, "rsrc")
lib_path = path.join(project_path, "importers", "lib")
sys.path.append( lib_path )
from importer_helpers import *

"""
"""

################################################################################
################################################################################
################################################################################

def main():
    """
    The `recordsSampler.py` script is used to create the example database
    `examplez` from an existing data set. It uses a standard Beacon query (with
    the `bycon` specific extensions such as global OR option for filters) and the
    `--limit` parameter to create a small, manageable data set from the corresponding
    number of random records pulled from the query results.

    The script will first create the database and then populate it with the records
    for the standrd entities. Optionally one can select to proceed with the additional
    steps for a CNV supporting database and create an archive for distribution.

    #### Examples

    * `.recordsSampler.py -d progenetix --output examplez --filters "pgx:icdom-81703,pgx:icdom-94003" --filterLogic OR  --limit 222`
    """
    
    # TODO: Hard coding this for now...
    examples_db = "examplez"

    BYC_PARS.update({"response_entity_path_id":"analyses"})
    BYC_PARS.update({"inputfile":"___dummy___"})
    BYC_PARS.update({"output": examples_db})

    proceed = input(f'Proceed with re-creating the example "{examples_db}" database? ? (y/N): ')
    if not "y" in proceed.lower():
        print("Exiting...")
        exit()
    set_entities()

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

    BRS = ByconResultSets()
    ds_results = BRS.datasetsResults()
    ByconautImporter(False).move_individuals_and_downstream_from_ds_results(ds_results)

    print(f"Finished re-creating the example database '{examples_db}'.")
    print(f"For full functionality you might want to run \n\n`{loc_path}/housekeeping.py -d {examples_db}`\n\nor continue with th efollowing commands.\n")

    proceed = input(f'Proceed with running the (time consuming) aggregation functions? (y/N): ')
    if not "y" in proceed.lower():
        exit()

    print(f'\n==> updating indexes for {examples_db}"')
    system(f'{loc_path}/mongodbIndexer.py -d {examples_db}')

    cmd = f'{loc_path}/collationsCreator.py -d {examples_db} --limit 0'
    print(f'\n==> executing\n\n{cmd}\n')
    system(cmd)

    cmd = f'{loc_path}/frequencymapsCreator.py -d {examples_db} --limit 0'
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

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
