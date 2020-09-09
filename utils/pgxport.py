#!/usr/local/bin/python3

import sys, yaml
from os import path as path
import argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *
from pgy import *

"""podmd

This program allows you to select biosamples from any of the datsets, and to export
the sample data in the format of
* a biosamples table
* callsets tables with the 1Mb status matrix data
* some statistics plots

Queries are handled through the standard `bycon` query aggregation. While some simple
parameters for data selection exist / may be added, the best way to filter the data is
through providing a JSON string with scoped queries, as if run directly against the
MongoDB collections.

CAVE: The ne version of the arguments parser makes it easier to copy/paste MongoDB 
terminal queries into a `queries` argument:

* regular expressions are converted from `/regex/` to `"regex"`
* operators are auto-quoted (`$and` => `"$and"`)

Please see the examples below.


##### Examples

* just one series
  - `bin/pgxport.py -q '{ "biosamples": {"external_references.type.id": "geogse-GSE67385"} }' -d arraymap`
* specific diagnosis from one publication, with export path
  - `bin/pgxport.py -q '{ "biosamples": { $and: [ { "biocharacteristics.type.id": "NCIT:C3209" }, {"external_references.type.id": "PMID:24037725"} ] } }' -p ~/groupbox/dbdata/out -d arraymap`
* combining this: all Progenetix samples with a "malignant" provenance and a numeric value in th efollowup
  - `bin/pgxport.py -q '{ "biosamples": { $and: [ { "info.followup_months": { $gte: 0 } }, { "provenance.material.type.id":"EFO:0009656" } ] } }' -p ~/groupbox/dbdata/out -d progenetix`
* cancer samples with fallback ISO country code:
  - `bin/pgxport.py -q '{ "biosamples": {$and: [ { "biocharacteristics.type.id":{ $regex: /icdom-[89]/ } }, {"provenance.geo.ISO-3166-alpha3": "XXX"} ] } }' -d arraymap -l cancers-missing-geo -o ../../dbdata`
* using "filters" (`-f`)
  - `bin/pgxport.py -f "NCIT:C" -d progenetix -l all-NCIT-mapped -o ../../dbdata`

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outdir", help="path to the output directory")
    parser.add_argument("-d", "--datasetid", help="dataset id")
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-q", "--queries", help="JSON query object")
    parser.add_argument("-a", "--dotalpha", help="dot opacity for plotting")
    parser.add_argument("-l", "--label", help="keyword label for output files")
    parser.add_argument("-t", "--test", help="test settings")
    parser.add_argument("-i", "--interactive", help="default prompt for customized outputs; 0 output biosamples table")

    args = parser.parse_args()

    return(args)

################################################################################

def _check_args(config, args):
  
    if not args.datasetid in config[ "dataset_ids" ]:
        print("No existing dataset was provided with -d ...")
        sys.exit()

    if not (args.filters or args.queries):
        print("No queries or filters were provided ...")
        sys.exit()

    if args.outdir:
        config[ "paths" ][ "out" ] = args.outdir
        
    if args.interactive == '0':
        config['prompt'] = False
    else:
        print('Default chosen interactive mode.')
        config['prompt'] = True

    if not path.isdir( config[ "paths" ][ "out" ] ):
        print("""
The output directory:
    {}
...does not exist; please use `-o` to specify
""".format(config[ "paths" ][ "out" ]))
        sys.exit( )

    return(config)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( path.abspath( dir_path ), '..', "data", "out" )

    args = _get_args()
    config = _check_args(config, args)

    kwargs = {
        "config": config,
        "args": args,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "h->o": read_named_prefs( "beacon_handovers", dir_path )
    }

    ds_id = args.datasetid

    print("=> files will be written to {}".format(config[ "paths" ][ "out" ]))
    print("=> looking up data in "+ds_id)

    kwargs[ "config" ].update( { "plot_pars": plotpars_from_args(**kwargs) } )
    kwargs.update( { "filters": parse_filters( **kwargs ) } )
    kwargs.update( { "queries": update_queries_from_filters(  { "queries": { } }, **kwargs ) } )
    kwargs.update( { "queries": pgx_queries_from_js(**kwargs) } )

    if not "queries" in kwargs:
        print('No query specified; please use "-h" for examples')
        sys.exit( )

    kwargs.update( { "query_results": execute_bycon_queries( ds_id, **kwargs ) } )
    query_results_save_handovers( **kwargs )

    if config['prompt']:
        if confirm_prompt("Export Biosamples table?", True):
            print("=> exporting biosamples")
            write_biosamples_table(**kwargs)

        if confirm_prompt("Export Callsets matrix files?", False):
            print("=> exporting matrix files")
            write_callsets_matrix_files(**kwargs)

        if confirm_prompt("Plot CNV statistics?", False):
            print("=> plotting CNV statistics")
            kwargs.update( { "callsets_stats": callsets_return_stats(ds_id, **kwargs) } )
            plot_callset_stats(ds_id, **kwargs)

        if confirm_prompt("Create sample map?", True):
            print("=> plotting map")
            plot_sample_geomap(**kwargs)
    else:
        write_biosamples_table(**kwargs)

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
