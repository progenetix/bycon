#!/usr/bin/env python3

from os import pardir, path, system
from bycon import *
from pymongo import MongoClient
from random import sample as random_samples

from bycon import byconServiceLibs
from importer_helpers import ByconautImporter
from service_helpers import assertSingleDatasetOrExit

loc_path = path.dirname( path.abspath(__file__) )
project_path = path.join(loc_path , pardir)
rsrc_path = path.join(project_path, "rsrc")

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
    for the standard entities. Optionally one can select to proceed with the additional
    steps for a CNV supporting database and create an archive for distribution.

    #### Examples

    * `.recordsSampler.py -d progenetix --output examplez --filters "pgx:icdom-81703,pgx:icdom-94003" --filterLogic OR  --limit 222`
    """
    
    # TODO: Hard coding this for now...
    ds_id = assertSingleDatasetOrExit()
    examples_db = "examplez"
    proceed = input(f'Proceed with re-creating the example "{examples_db}" database? ? (y/N): ')
    if not "y" in proceed.lower():
        print("Exiting...")
        exit()
    set_entities()

    example_queries = BYC.get("test_queries", {})

    BYC_PARS.update({"response_entity_path_id":"analyses"})
    BYC_PARS.update({"inputfile":"___dummy___"})
    BYC_PARS.update({"output": examples_db})

    # TODO: prototyping use of a seies of queries to collect matching
    # individuals & subsampling those. 
    ana_ids = set()
    for qek, qev in example_queries.items():
        for p, v in qev.items():
            if p == "filters":
                f_l = []
                for f in v:
                    f_l.append({"id": f})
                if len(f_l) > 0:
                    BYC.update({"BYC_FILTERS":f_l})
            else:
                BYC_PARS.update({p: v})

        print(f'... getting data for {qek}')
        BRS = ByconResultSets()
        # print(BRS.get_record_queries())
        ds_results = BRS.datasetsResults()
        print(f'... got it')

        # clean out those globals for next run
        # filters are tricky since they have a default `[]` value
        # and have been pre-parsed into BYC_FILTERS at the stage of
        # `ByconResultSets()` (_i.e._ embedded `ByconQuery()`)
        for p, v in qev.items():
            if p == "filters":
                BYC_PARS.update({"filters": []})
            else:
                BYC_PARS.pop(p)
        BYC.update({"BYC_FILTERS": []})
        
        if not (ds := ds_results.get("progenetix")):
            continue

        f_i_ids = ds["analyses.id"].get("target_values", [])
        ana_ids.update(random_samples(f_i_ids, min(BYC_PARS.get("limit", 200), len(f_i_ids))))
        print(f'==> now {len(ana_ids)}')

    BYC_PARS.update({"analysis_ids": list(ana_ids)})    

    BRS = ByconResultSets()
    ds_results = BRS.datasetsResults()
    if not (ds := ds_results.get("progenetix")):
        return

    a_i_ids = ds["individuals.id"].get("target_values", [])
    proceed = input(f'Proceed importing {len(a_i_ids)} and depending records? (y/N): ')
    if not "y" in proceed.lower():
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

    ByconautImporter(False).move_individuals_and_downstream_from_ds_results(ds_results)

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

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
