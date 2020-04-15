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

"""
https://progenetix.test/cgi/bycon/cgi/cytomap.py?assemblyId=GRCh38&cytoband=8q24.1&referenceName=17
https://progenetix.test/cgi/bycon/cgi/cytomap.py?assemblyId=GRCh38&referenceName=17&start=8000000&end=24326000
"""

################################################################################
################################################################################
################################################################################

# cgitb.enable()  # for debugging

################################################################################

def main():

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

    # TODO: "byc" becoming a proper object?!
    byc = {
        "config": config,
        "opts": opts,
        "form_data": form_data
    }

    cyto_response = {
        "assemblyId": "",
        "cytoband": "",
        "referenceName": None,
        "start": None,
        "end": None,
        "error": None
    }
 
    byc[ "variant_defs" ], byc[ "variant_request_types" ] = read_variant_definitions( **byc )
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc["variant_pars"][ "variantType" ] =  "CNV"
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    
    cb_re = re.compile( byc["variant_defs"][ "cytoband" ][ "pattern" ] )

    cyto_response[ "assemblyId" ] = byc["variant_pars"][ "assemblyId" ]

    if not byc[ "variant_request_type" ] == "beacon_range_request":
        if "cytoband" in byc["variant_pars"]:
            cb_par = str( byc["variant_pars"][ "cytoband" ] )
            if cb_re.match( cb_par ):
                byc[ "variant_request_type" ] = "cytoband_mapping"
        else:
            cyto_response[ "error" ] = "¡No mapping query!"
            cgi_print_json_response(cyto_response)

    genome = byc["variant_pars"][ "assemblyId" ].lower()
    cb_file = path.join( byc[ "config" ][ "paths" ][ "genomes" ], genome, "CytoBandIdeo.txt" )
    
    cytobands = parse_cytoband_file( cb_file )

    if byc[ "variant_request_type" ] == "cytoband_mapping":
        chro, cb_start, cb_end = cb_re.match(cb_par).group(2, 3, 7)
        cyto_response[ "cytoband" ] = cb_par
        cytobands = subset_cytobands(  cytobands, chro, cb_start, cb_end  )
        if len(cytobands) < 1:
            cyto_response[ "error" ] = "No matching cytobands!"
        else:
            cyto_response.update( {
                "referenceName": chro,
                "start": cytobands[0]["start"],
                "end": cytobands[-1]["end"],
                "cytoband": cytobands[0]["chro"]+cytobands[0]["cytoband"]
            } )
            if len(cytobands) > 1:
                cyto_response.update( { "cytoband":  cyto_response[ "cytoband" ]+cytobands[-1]["cytoband"] } )

    elif byc[ "variant_request_type" ] == "beacon_range_request":
        chro = byc["variant_pars"][ "referenceName" ]
        start = int( byc["variant_pars"][ "start" ] )
        end = int( byc["variant_pars"][ "end" ] )
        cytobands = subset_cytobands_by_bases(  cytobands, chro, start, end  )
        if len(cytobands) < 1:
            cyto_response[ "error" ] = "No matching cytobands!"
        else:
            cyto_response.update( {
                "referenceName": chro,
                "start": start,
                "end": end,
                "cytoband": cytobands[0]["chro"]+cytobands[0]["cytoband"]
            } )
            if len(cytobands) > 1:
                cyto_response.update( { "cytoband":  cyto_response[ "cytoband" ]+cytobands[-1]["cytoband"] } )

    cgi_print_json_response(cyto_response)

################################################################################
################################################################################

if __name__ == '__main__':
    main()
