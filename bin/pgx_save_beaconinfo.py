#!/usr/local/bin/python3

import json, yaml
from os import path as path
from os import environ
import sys, os, datetime, logging, argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""

This script reads the Becon definitions from the configuration file, populates
the filter definition and dataset statistics and saves the enriched beacon info
as YAML file, to be read in by the `byconplus` web service.

"""

################################################################################
################################################################################
################################################################################

def main():
    
    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    ofp = path.join( config[ "paths" ][ "module_root" ], *config[ "paths" ][ "beacon_info_file" ] )

    # input & definitions

    byc = {
        "config": config,
        "get_filters": True
    }

    byc.update( { "filter_defs": read_filter_definitions( **byc ) } )
    byc.update( { "dbstats": dbstats_return_latest( **byc ) } )
    byc.update( { "service_info": generate_beacon_info( **byc ) } )

    with open(ofp, 'w') as of:
        yaml.dump(byc["service_info"], of)

    print("=> output written to {}".format(ofp))
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
