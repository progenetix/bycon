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

"""podmd

* `bin/pgx_update_mappings.py -d arraymap -m rsrc/ICDOntologies.ods`

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outdir", help="path to the output directory")
    parser.add_argument("-i", "--icdomappath", help="path to the ICD mapping directory")    
    parser.add_argument("-d", "--datasetid", help="dataset id")
    parser.add_argument("-m", "--mappingfile", help="update file with canonical headers to be used instead of the default mapping file")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( config[ "paths" ][ "module_root" ], "data", "out" )
    config[ "paths" ][ "mapping_file" ] = path.join( config[ "paths" ][ "module_root" ], *config[ "paths" ][ "icd-ncit-mapping_file" ] )

    args = _get_args()

    ds_id = args.datasetid
    if not ds_id in config[ "dataset_ids" ]:
        print("No existing dataset was provided with -d ...")
        exit()

    try:
        if path.isdir( args.outdir ):
            config[ "paths" ][ "out" ] = args.outdir
    except:
        pass
    try:
        if path.isdir( args.icdomappath ):
            config[ "paths" ][ "icdomappath" ] = args.icdomappath
    except:
        pass
    try:
        if path.isfile( args.mappingfile ):
            config[ "paths" ][ "mapping_file" ] = args.mappingfile
    except:
        pass

    kwargs = {
        "config": config,
        "args": args,
        "update_collection": "biosamples",
        "filter_defs": read_filter_definitions( **config[ "paths" ] ) 
    }
    
    ############################################################################

    if confirm_prompt("Update Default Mappings?", False):
 
        if not path.isfile(config[ "paths" ][ "mapping_file" ]):
            print("No mapping file was provided with -m ...")
        else:        
            kwargs["defmaps"] = pgx_read_icdom_ncit_defaults( **kwargs)
            kwargs["equiv_keys"], kwargs["equivmaps"] = pgx_read_mappings( **kwargs)
                        
            pgx_write_mappings_to_yaml( **kwargs )
            pgx_rewrite_icdmaps_db( **kwargs )
            od = pgx_update_biocharacteristics( ds_id, **kwargs)
                    
            of = path.join( config[ "paths" ][ "module_root" ], "data", "out", "logs", date.today().isoformat()+"_pgxupdate_mappings_report_"+ds_id+".tsv")
            write_tsv_from_list(of, od, **config)

    ############################################################################

    if confirm_prompt("Save Current Mappings?", False):
 
        kwargs["equiv_keys"], kwargs["equivmaps"] = pgx_read_mappings( **kwargs)
                    
        od = get_current_mappings( **kwargs)
        of = path.join( config[ "paths" ][ "module_root" ], "rsrc", "icdo", "ICDO_mappings_current.tsv")
        write_tsv_from_list(of, od, **config)
        print("=> wrote mappings to {}".format(of))

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
