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
    config[ "paths" ][ "mod_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( path.abspath( dir_path ), '..', "data", "out" )
    config[ "paths" ][ "mapping_file" ] = path.abspath(".")

    opts, args = get_cmd_args()

    for opt, arg in opts:
        if opt in ("-f", "--mappingfile"):
            config[ "paths" ][ "mapping_file" ] = path.abspath(arg)        

    if not path.isfile(config[ "paths" ][ "mapping_file" ]):
        print("No existing file was provided with -f ...")
        exit()
    
    filter_defs = read_filter_definitions( **{ "config": config } )
    
    kwargs = { "config": config, "filter_defs": filter_defs }
    equivmaps = pgx_read_mappings( **kwargs)
    
    for dataset_id in config[ "dataset_ids" ]:
        kwargs = { "config": config, "filter_defs": filter_defs, "equivmaps": equivmaps, "dataset_id": dataset_id, "update_collection": "biosamples", "mapping_type": "icdo2ncit" }
        update_report = pgx_update_biocharacteristics(**kwargs)
    
        kwargs = { "config": config, "output_file": path.join( config[ "paths" ][ "mod_root" ], "data", "out", date.today().isoformat()+"_pgxupdate_mappings_report_"+dataset_id+".tsv"), "output_data": update_report }
        write_tsv_from_list(**kwargs)

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
