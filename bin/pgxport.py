#!/usr/local/bin/python3

import sys, yaml
from os import path as path

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""podmd

##### Examples

* `bin/pgxport.py -j '{ "biosamples": {"external_references.type.id": "geo:GSE67385"} }'

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( path.abspath( dir_path ), '..', "data", "out" )

    opts, args = get_cmd_args()

    dataset_ids = config[ "dataset_ids" ]
    for opt, arg in opts:
        if opt in ("-f", "--mappingfile"):
            config[ "paths" ][ "mapping_file" ] = path.abspath(arg)        
        if opt in ("-d", "--dataset_ids"):
            dataset_ids = arg.split(',')
        if opt in ("-p", "--outpath"):
            if path.isdir( arg ):
                config[ "paths" ][ "out" ] = arg
    
    if not dataset_ids:
        print("No existing dataset_id was provided with -d ...")
        exit()
    if not path.isdir( config[ "paths" ][ "out" ] ):
        print("The output directory:\n\t"+config[ "paths" ][ "out" ]+"\n...does not exist; please use `-p` to specify")
        sys.exit( )
    else:
        print("=> files will be written to"+str(config[ "paths" ][ "out" ]))

    print("=> looking up data in "+dataset_ids[0])

    kwargs = { "config": config, "dataset_id": dataset_ids[0], "filter_defs": read_filter_definitions( **{ "config": config } ), "queries": pgx_queries_from_args(opts) }

    if not kwargs["queries"]:
        print('No query specified; please use "-h" for examples')
        sys.exit( )

    kwargs[ "config" ].update( { "plot_pars": plotpars_from_args(opts, **kwargs) } )
    kwargs[ "config" ].update( { "data_pars": pgx_datapars_from_args(opts, **kwargs) } )

    query_results = execute_bycon_queries(**kwargs)

    kwargs.update( { "callsets::_id": query_results["callsets::_id"] } )
    kwargs.update( { "biosamples::_id": query_results["biosamples::_id"] } )
 
    write_biosamples_table(**kwargs)
    write_callsets_matrix_files(**kwargs)

    kwargs.update( { "callsets_stats": callsets_return_stats(**kwargs) } )

    plot_callset_stats(**kwargs)

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
