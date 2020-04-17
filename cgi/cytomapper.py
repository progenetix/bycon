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
from bycon.cgi_parse_variant_requests import *
from bycon.cgi_utils import *
from bycon.cmd_parse_args import *
from bycon.cytoband_utils import *


"""podmd

This script parses either:

* a "Beacon-style" positional request (`assemblyId`, `referenceName`, `start`, `end`), to retrieve
overlapping cytobands, or
* a properly formatted cytoband annotation (`assemblyId`, `cytoband`)
  - "8", "9p11q21", "8q", "1p12qter"
* a concatenated `chroBases` parameter
  - `7:23028447-45000000`
  - `X:99202660`

There is a fallback to *GRCh38* if no assembly is being provided.

The `cytoband` and `chroBases` parameters can be used for running the script on the command line
(see examples below).


#### Examples

* retrieve coordinates for some bands on chromosome 8
  - <https://progenetix.org/cgi/bycon/cgi/cytomapper.py?assemblyId=NCBI36.1&cytoband=8q>
* get the cytobands whith which a base range on chromosome 17 overlaps, in short and long form
  - <https://progenetix.org/cgi/bycon/cgi/cytomapper.py?assemblyId=GRCh38&referenceName=17&start=800000&end=24326000>
  - <https://progenetix.org/cgi/bycon/cgi/cytomapper.py?assemblyId=NCBI36&chroBases=17:800000-24326000>  
* command line version of the above
  - `cgi/cytomapper.py --chroBases 17:800000-24326000 --g NCBI36`

#### TODO

* fallback to info / documentation
* better error capture & documentation (e.g. wrong assemblies ...)
* warning about / correcting wrong cytoband syntax (e.g. *not* "17p11p12" *but* "17p12p11")

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
    byc.update( { "variant_pars": _parse_chrobases( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    byc.update( { "cytobands": parse_cytoband_file( **byc ) } )
    byc["cytobands"], byc["variant_pars"][ "referenceName" ], cb_label = filter_cytobands( **byc )

    # response prototype
    cyto_response = {
        "request": byc["variant_pars"],
        "assemblyId": byc["variant_pars"][ "assemblyId" ],
        "cytobands": cb_label,
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
    } )

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

def _parse_chrobases( **byc ):

    variant_pars = byc["variant_pars"]
    variant_defs = byc["variant_defs"]
    v_par = "chroBases"

    if v_par in variant_pars:
        cb_re = re.compile( variant_defs[ v_par ][ "pattern" ] )
        chro, start, end = cb_re.match( byc["variant_pars"][ v_par ] ).group(2, 3, 5)
        if not end:
            end = int(start) + 1
        variant_pars[ "referenceName" ], variant_pars[ "start" ], variant_pars[ "end" ] = chro, int(start), int(end)
        variant_pars[ "rangeTag" ] = "true"

    return(variant_pars)

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
