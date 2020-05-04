#!/usr/local/bin/python3

import sys, yaml
from os import path as path
import argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

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

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--outdir", help="path to the output directory")
    parser.add_argument("-d", "--datasetid", help="dataset id")
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-b", "--bioclass", help="prefixed filter values, comma concatenated")
    parser.add_argument("-e", "--extid", help="prefixed filter values, comma concatenated")    
    parser.add_argument("-q", "--queries", help="JSON query object")
    parser.add_argument("-a", "--dotalpha", help="dot opacity for plotting")
    parser.add_argument("-l", "--label", help="keyword label for output files")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( path.abspath( dir_path ), '..', "data", "out" )

    args = _get_args()

    dataset_id = args.datasetid
    try:
        if path.isdir( args.outdir ):
            config[ "paths" ][ "out" ] = args.outdir
    except:
        pass

    if not dataset_id in config[ "dataset_ids" ]:
        print("No existing dataset was provided with -d ...")
        exit()
    if not path.isdir( config[ "paths" ][ "out" ] ):
        print("The output directory:\n\t"+config[ "paths" ][ "out" ]+"\n...does not exist; please use `-p` to specify")
        sys.exit( )
    else:
        print("=> files will be written to"+str(config[ "paths" ][ "out" ]))

    print("=> looking up data in "+dataset_id)

    kwargs = {
        "config": config,
        "args": args,
        "dataset_id": dataset_id,
        "filter_defs": read_filter_definitions( **{ "config": config } )
    }
    
    kwargs.update( { "queries": pgx_queries_from_args(**kwargs) } )

    if not "queries" in kwargs:
        print('No query specified; please use "-h" for examples')
        sys.exit( )

    kwargs[ "config" ].update( { "plot_pars": plotpars_from_args(**kwargs) } )

    query_results = execute_bycon_queries(**kwargs)

    kwargs.update( { "callsets::_id": query_results["callsets::_id"] } )
    kwargs.update( { "biosamples::_id": query_results["biosamples::_id"] } )
    
    if confirm_prompt("Export Biosamples table?", True):
        print("=> exporting biosamples")
        write_biosamples_table(**kwargs)

    if confirm_prompt("Export Callsets matrix files?", False):
        print("=> exporting matrix files")
        write_callsets_matrix_files(**kwargs)

    if confirm_prompt("Plot CNV statistics?", False):
        print("=> plotting CNV statistics")
        kwargs.update( { "callsets_stats": callsets_return_stats(**kwargs) } )
        plot_callset_stats(**kwargs)

    if confirm_prompt("Create geographic map?", False):
        print("=> plotting map")
        plot_worldmap(**kwargs)


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
