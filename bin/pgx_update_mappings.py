#!/usr/local/bin/python3

import time
from datetime import date
import sys, yaml
from os import path as path


# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

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
    kwargs = { "config": config }
    kwargs[ "config" ][ "data_pars" ] = pgx_datapars_from_args(opts, **kwargs)

    dataset_ids = config[ "dataset_ids" ]
    for opt, arg in opts:
        if opt in ("-f", "--mappingfile"):
            config[ "paths" ][ "mapping_file" ] = path.abspath(arg)        
        if opt in ("-y", "--icdomappath"):
            config[ "paths" ][ "icdomappath" ] = path.abspath(arg)        
        if opt in ("-d", "--dataset_ids"):
            dataset_ids = arg.split(',')


    for dataset_id in dataset_ids:
        print(dataset_id)
        kwargs = { "config": config, "dataset_id": dataset_id, "update_collection": "biosamples" }
        pgx_normalize_prefixed_ids( **kwargs )
        
    # exit()





    if not path.isfile(config[ "paths" ][ "mapping_file" ]):
        print("No existing file was provided with -f ...")
        exit()
        
    if not dataset_ids:
        print("No existing dataset_id was provided with -d ...")
        exit()
   
    filter_defs = read_filter_definitions( **{ "config": config } )    
    kwargs = { "config": config, "filter_defs": filter_defs }
    equiv_keys, equivmaps = pgx_read_mappings( **kwargs)
    
    kwargs = { "config": config, "filter_defs": filter_defs, "equiv_keys": equiv_keys, "equivmaps": equivmaps }
    
    pgx_write_mappings_to_yaml( **kwargs)
    
    for dataset_id in dataset_ids:
        if not dataset_id in config[ "dataset_ids" ]:
            print(dataset_id+" does not exist")
            continue
            
        kwargs = { "config": config, "filter_defs": filter_defs, "equiv_keys": equiv_keys, "equivmaps": equivmaps, "dataset_id": dataset_id, "update_collection": "biosamples", "mapping_type": "icdo2ncit" }
        update_report = pgx_update_biocharacteristics(**kwargs)
    
        kwargs = { "config": config, "output_file": path.join( config[ "paths" ][ "module_root" ], "data", "out", "logs", date.today().isoformat()+"_pgxupdate_mappings_report_"+dataset_id+".tsv"), "output_data": update_report }
        write_tsv_from_list(**kwargs)

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
