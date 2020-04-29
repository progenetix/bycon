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

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outdir", help="path to the output directory")
    parser.add_argument("-i", "--icdomappath", help="path to the ICD mapping directory")    
    parser.add_argument("-d", "--datasetid", help="dataset id")
    parser.add_argument("-m", "--mappingfile", help="update file with canonical headers")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( path.abspath( dir_path ), '..', "data", "out" )
    config[ "paths" ][ "mapping_file" ] = path.abspath(".")

    args = _get_args()

    dataset_id = args.datasetid
    if not dataset_id in config[ "dataset_ids" ]:
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
        "dataset_id": dataset_id,
        "update_collection": "biosamples",
        "filter_defs": read_filter_definitions( **{ "config": config } ) 
    }
    
    ############################################################################

    if confirm_prompt("Update Biosamples from File?", False):

        print("=> updating biosamples")
        pgx_update_samples_from_file( **kwargs )

    ############################################################################

    if confirm_prompt("Normalize Prefixes?", False):

        print("=> normalizing prefixes")
        pgx_normalize_prefixed_ids( **kwargs )

    ############################################################################

    if confirm_prompt("Update Mappings?", False):
 
        if not path.isfile(config[ "paths" ][ "mapping_file" ]):
            print("No mapping file was provided with -f ...")
        else:        
            kwargs["equiv_keys"], kwargs["equivmaps"] = pgx_read_mappings( **kwargs)
                        
            pgx_write_mappings_to_yaml( **kwargs)
            
            kwargs.update( { "mapping_type": "icdo2ncit" } )
        
            kwargs.update( {
                "output_file": path.join( config[ "paths" ][ "module_root" ], "data", "out", "logs", date.today().isoformat()+"_pgxupdate_mappings_report_"+dataset_id+".tsv"),
                "output_data": pgx_update_biocharacteristics(**kwargs)
            } )
            write_tsv_from_list(**kwargs)

    ############################################################################

    if confirm_prompt("Denormalize Biosample Essentials Into Callsets?", False):

        print("=> denormalizing into callsets")
        pgx_populate_callset_info( **kwargs )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
