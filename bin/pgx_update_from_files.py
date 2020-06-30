#!/usr/local/bin/python3

import time
from datetime import date
import sys, yaml
from os import path as path
import argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *
from pgy import *

# TODO: Interactive selection of procedures

"""podmd

* `bin/pgx_update_from_files.py -u ~/dbtools/bycon/data/in/biosamples_update.ods -d arraymap`
* `bin/pgx_update_from_files.py -u ~/switchdrive/baudisgroup/collaborations/Bellinzona/2020-04-22-PMID-24037725-for-Francesco/progenetix-277-biosamples.tsv -d progenetix`

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outdir", help="path to the output directory")
    parser.add_argument("-d", "--datasetid", help="dataset id")
    parser.add_argument("-u", "--updatefile", help="update file with canonical headers")
    parser.add_argument("-t", "--test", help="test setting")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( path.abspath( dir_path ), '..', "data", "out" )

    write_biosamples_template_file(**config)

    args = _get_args()
    config[ "paths" ][ "update_file" ] = args.updatefile
    ds_id = args.datasetid

    try:
        if path.isdir( args.outdir ):
            config[ "paths" ][ "out" ] = args.outdir
    except:
        pass

    if not ds_id in config[ "dataset_ids" ]:
        print("No existing dataset was provided with -d ...")
        exit()
    try:
        if path.isfile( args.updatefile ):
            config[ "paths" ][ "update_file" ] = args.updatefile
    except:
        print("No existing update file was provided with -u ...")
        sys.exit()
    if not  path.isdir( config[ "paths" ][ "out" ] ):
        print("No existing output directory was provided with -o ...")
        sys.exit()

    ############################################################################

    kwargs = {
        "config": config,
        "args": args,
        "update_collection": "biosamples",
        "filter_defs": read_filter_definitions( **config[ "paths" ] ) 
    }

   
    if confirm_prompt("""Update Biosamples in {} from file\n{}\n""".format(ds_id, kwargs[ "config" ][ "paths" ][ "update_file" ]), False):

        print("=> updating biosamples in "+ds_id)
        pgx_update_samples_from_file( ds_id, **kwargs )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
