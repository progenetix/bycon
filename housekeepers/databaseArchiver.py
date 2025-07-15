#!/usr/local/bin/python3

from os import path, pardir, mkdir, system
from datetime import datetime
import shutil
from isodate import date_isoformat
from uuid import uuid4

from bycon import BYC, BYC_PARS
from byconServiceLibs import assert_single_dataset_or_exit

################################################################################

def main():
    ds_id = assert_single_dataset_or_exit()

    output_dir = BYC_PARS.get("outputdir")
    if not output_dir:
        print("No output directory specified (--outputdir) => quitting ...")
        exit()
    elif not path.isdir(output_dir):
        print("Output directory does not exist => quitting ...")
        exit()   

    ############################################################################

    tmp_dir = path.join(output_dir, f'{str(uuid4())}')
    mkdir(tmp_dir)
    for db in [ds_id, "_byconServicesDB"]:
        db_tmp = path.join( tmp_dir, db )
        e_ds_archive = f'{db}.tar.gz'
        system(f'rm -rf {db_tmp}')
        system(f'mongodump --db {db} --out {tmp_dir}')
    sysCmd = f'cd {output_dir} && tar -czf {date_isoformat(datetime.now())}-{ds_id}.tar.gz {ds_id} && rm -rf {tmp_dir}'
    print(sysCmd)
    system(sysCmd)

################################################################################

if __name__ == '__main__':
    main()
