#!/usr/local/bin/python3

import time
from datetime import date
import sys, yaml
from os import path as path


# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

# TODO: Interactive selection of procedures

"""podmd

* `bin/pgx_update_from_files.py -f /Users/bgadmin/dbtools/bycon/data/in/biosamples_update.ods -d arraymap`
* `bin/pgx_update_from_files.py -f /Users/mbaudis/switchdrive/baudisgroup/collaborations/Bellinzona/2020-04-22-PMID-24037725-for-Francesco/progenetix-277-biosamples.tsv -d progenetix`

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( path.abspath( dir_path ), '..', "data", "out" )
    config[ "paths" ][ "mapping_file" ] = path.abspath(".")

    opts, args = get_cmd_args()
    kwargs = { "config": config, "filter_defs": read_filter_definitions( **{ "config": config } )  }
    kwargs[ "config" ][ "data_pars" ] = pgx_datapars_from_args(opts, **kwargs)

    dataset_ids = config[ "dataset_ids" ]
    for opt, arg in opts:
        if opt in ("-f", "--mappingfile"):
            kwargs[ "config" ][ "paths" ][ "mapping_file" ] = path.abspath(arg)        
        if opt in ("-d", "--dataset_ids"):
            dataset_ids = arg.split(',')
    
    if not dataset_ids:
        print("No existing dataset_id was provided with -d ...")
        exit()

    dataset_id = dataset_ids[0]
    if len(dataset_ids) > 1:
        print("¡¡¡ Only the first dataset "+dataset_id+" is being processed !!!")
   
    ############################################################################

    if confirm_prompt("Update Biosamples from File?", False):

        print("=> updating biosamples in "+dataset_id)
        kwargs.update( { "dataset_id": dataset_id, "update_collection": "biosamples" } )
        pgx_update_samples_from_file( **kwargs )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
