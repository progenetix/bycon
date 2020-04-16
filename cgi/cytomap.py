#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import path as path
import sys
import datetime
import csv

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *


"""podmd

This script parses either:

* a "Beacon-style" positional request (`assemblyId`, `referenceName`, `start`, `end`), to retrieve
overlapping cytobands, or
* a properly formatted cytoband annotation (`assemblyId`, `cytoband`)
    - "8", "9p11q21", "8q"

#### Examples

* retrieve coordinates for some bands on chromosome 8
  - <https://progenetix.org/cgi/bycon/cgi/cytomap.py?assemblyId=NCBI36.1&cytoband=8q>
* get the cytobands whith which a base range on chromosome 17 overlaps
  - <https://progenetix.org/cgi/bycon/cgi/cytomap.py?assemblyId=GRCh38&referenceName=17&start=800000&end=24326000>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    # cgitb.enable()  # for debugging
    # print('Content-Type: text')
    # print()
    
    # input & definitions
    form_data = cgi_parse_query()
    opts, args = get_cmd_args()

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.abspath( config[ "paths" ][ "web_temp_dir_abs" ] )
    config[ "paths" ][ "genomes" ] = path.join( config[ "paths" ][ "module_root" ], "rsrc", "genomes" )

    byc = {
        "config": config,
        "opts": opts,
        "form_data": form_data
    }

    byc[ "variant_defs" ], byc[ "variant_request_types" ] = read_variant_definitions( **byc )
    byc.update( { "variant_pars": parse_variants( **byc ) } )

    byc["variant_pars"][ "rangeTag" ] = "true"

    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    byc.update( { "cytobands": parse_cytoband_file( **byc ) } )
    byc["cytobands"], byc["variant_pars"][ "referenceName" ] = filter_cytobands( **byc )

    # response prototype
    cyto_response = {
        "request": byc["variant_pars"],
        "assemblyId": byc["variant_pars"][ "assemblyId" ],
        "cytoband": None,
        "referenceName": byc["variant_pars"][ "referenceName" ],
        "start": None,
        "end": None,
        "size": None,
        "error": None
    }

    if len( byc["cytobands"] ) < 1:
        cyto_response[ "error" ] = "No matching cytobands!"
        cgi_print_json_response(cyto_response)

    cyto_response.update( {
        "start": int( byc["cytobands"][0]["start"] ),
        "end": int( byc["cytobands"][-1]["end"] ),
        "cytoband": byc["cytobands"][0]["chro"]+byc["cytobands"][0]["cytoband"]
    } )
    if len( byc["cytobands"] ) > 1:
        cyto_response.update( { "cytoband":  cyto_response[ "cytoband" ]+byc["cytobands"][-1]["cytoband"] } )

    if byc[ "variant_request_type" ] == "positions2cytobands_request":
        cyto_response.update( {
            "start": int( byc["variant_pars"][ "start" ] ),
            "end": int( byc["variant_pars"][ "end" ] ),
        } )
        
    cyto_response.update( { "size":  int( cyto_response[ "end" ] - cyto_response[ "start" ] ) } )

    if "callback" in byc[ "form_data" ]:
        cgi_print_json_callback(byc["form_data"].getvalue("callback"), [cyto_response])
    else:
        cgi_print_json_response(cyto_response)

################################################################################
################################################################################

if __name__ == '__main__':
    main()
