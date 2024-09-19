#!/usr/bin/env python3

from pymongo import MongoClient
from os import path, pardir, mkdir, system, environ
import datetime, shutil
from pathlib import Path
from isodate import date_isoformat

from bycon import *

dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )

################################################################################
################################################################################
################################################################################

def main():
    """
    ./bin/database_archiver -d progenetix
    """
    database_archiver()

################################################################################

def database_archiver():
    initialize_bycon_service()

    if len(BYC["BYC_DATASET_IDS"]) != 1:
        print("No single existing dataset was provided with -d ...")
        exit()
    ds_id = BYC["BYC_DATASET_IDS"][0]

    output_dir = BYC_PARS.get("outputdir")
    if not output_dir:
        print("No output directory specified (--outputdir) => quitting ...")
        exit()
    elif not path.isdir(output_dir):
        print("Output directory does not exist => quitting ...")
        exit()   

    ############################################################################

    tmp_dir = path.join( output_dir, ds_id )
    if path.isdir(tmp_dir):
        shutil.rmtree(tmp_dir)
    mkdir(tmp_dir)
    for db in [ds_id, "_byconServicesDB"]:
        db_tmp = path.join( tmp_dir, db )
        e_ds_archive = f'{db}.tar.gz'
        system(f'rm -rf {db_tmp}')
        system(f'mongodump --db {db} --out {tmp_dir}')
    sysCmd = f'cd {output_dir} && tar -czf {date_isoformat(datetime.datetime.now())}-{ds_id}.tar.gz {ds_id} && rm -rf {tmp_dir}'
    print(sysCmd)
    system(sysCmd)

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
