#!/usr/local/bin/python3

import cgi, cgitb
import re, yaml
from os import path, pardir
import csv
import sys, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from beaconServer.lib.cgi_utils import *
from beaconServer.lib.parse_variants import *
from beaconServer.lib.read_specs import *
from lib.cytoband_utils import *
from beaconServer.lib.service_utils import *

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cytobands", help="cytoband(s), e.g. `8q21q24.1`")
    parser.add_argument("-b", "--chrobases", help="chromosome and base(s), e.g. `17:12003942-18903371`")
    parser.add_argument("-g", "--genome", help="genome edition, e.g. `GRCh38`")
    args = parser.parse_args()

    return args

################################################################################

def main():

    cytomapper()

################################################################################
################################################################################
################################################################################

def cytomapper():
    
    byc = initialize_service()

    local_path = path.dirname( path.abspath(__file__) )
    byc.update( { "args": _get_args() } )
    byc[ "config" ][ "paths" ][ "genomes" ] = path.join( local_path, "rsrc", "genomes" )
    
    parse_variants(byc)
    generate_genomic_intervals(byc, "cytobands")

    # response prototype
    create_empty_service_response(byc)

    cytoBands = [ ]
    if "cytoBands" in byc["variant_pars"]:
        cytoBands, chro, start, end = _bands_from_cytobands(byc)
        byc["service_response"]["meta"]["received_request"].update({ "cytoBands": byc["variant_pars"]["cytoBands"] })
    elif "chroBases" in byc["variant_pars"]:
        cytoBands, chro, start, end = _bands_from_chrobases(byc)
        byc["service_response"]["meta"]["received_request"].update({ "chroBases": byc["variant_pars"]["chroBases"] })

    cb_label = _cytobands_label( cytoBands )

    if len( cytoBands ) < 1:
        response_add_error(byc, 422, "No matching cytobands!" )
        _print_terminal_response( byc )
        cgi_break_on_errors(byc)

    size = int(  end - start )
    chroBases = chro+":"+str(start)+"-"+str(end)
    
    results = [
        {
            "info": {
                "cytoBands": cb_label,
                "bandList": [x['chroband'] for x in cytoBands ],
                "chroBases": chroBases,
                "referenceName": chro,
                "size": size,
            },        
            "ChromosomeLocation": {
                "type": "ChromosomeLocation",
                "species_id": "taxonomy:9606",
                "chr": chro,
                "interval": {
                    "start": cytoBands[0]["cytoband"],
                    "end": cytoBands[-1]["cytoband"],
                    "type": "CytobandInterval"
                }
            },
            "GenomicLocation": {
                "type": "GenomicLocation",
                "species_id": "taxonomy:9606",
                "chr": chro,
                "interval": {
                    "start": start,
                    "end": end,
                    "type": "SimpleInterval"
                }
            }
        }
    ]

    _print_terminal_response( byc["args"], byc["service_response"] )

    populate_service_response( byc, results)
    cgi_print_json_response( byc, 200 )

################################################################################

def _bands_from_cytobands(byc):

    chr_bands = byc["variant_pars"]["cytoBands"]
    cb_pat = re.compile( byc["variant_definitions"]["parameters"]["cytoBands"]["pattern"] )
    chro, cb_start, cb_end = cb_pat.match(chr_bands).group(2,3,9)
    if not cb_end:
        cb_end = cb_start

    cytobands = list(filter(lambda d: d[ "chro" ] == chro, byc["cytobands"]))
    if cb_start == None and cb_end == None:
        return cytobands, chro

    cb_from = 0
    cb_to = len(cytobands)

    if cb_start == None or cb_start == "pter":
        cb_start = "p"
    if cb_end == "qter":
        cb_end = "q"
    if cb_end == "pcen":
        cb_end = "p"
    if cb_start == "qcen":
        cb_start = "q"
    if cb_start == "pcen":
        cb_start = "q"

    cb_s_re = re.compile( "^"+cb_start )
    i = 0

    # searching for the first matching band
    for cb in cytobands:
        if cb_s_re.match( cb[ "cytoband" ] ):
            cb_from = i
            break
        i += 1
    k = 0

    # retrieving the last matching band
    # * index at least as start to avoid "q21qter" => "all q"
    # * if there was no end, the start band is queried again until its last match
    if cb_end == None:
        cb_end = cb_start

    cb_e_re = re.compile( "^"+cb_end )

    for cb in cytobands:
        if k >= i:
            if cb_e_re.match( cb[ "cytoband" ] ):
                cb_to = k+1
        k += 1

    cytobands = cytobands[cb_from:cb_to]

    return cytobands, chro, int( cytobands[0]["start"] ), int( cytobands[-1]["end"] )

################################################################################

def _bands_from_chrobases( byc ):

    chr_bases = byc["variant_pars"]["chroBases"]
    cb_pat = re.compile( byc["variant_definitions"]["parameters"]["chroBases"]["pattern"] )

    chro, cb_start, cb_end = cb_pat.match(chr_bases).group(2,3,5)
    if cb_start:
        cb_start = int(cb_start)
        if not cb_end:
            cb_end = cb_start + 1
        cb_end = int(cb_end)

    cytobands = list(filter(lambda d: d[ "chro" ] == chro, byc["cytobands"]))
    if cb_start == None:
        cb_start = 0
    if cb_end == None:
        cb_end = int( cytoBands[-1]["end"] )

    if isinstance(cb_start, int):
        cytobands = list(filter(lambda d: int(d[ "end" ]) > cb_start, cytobands))

    if isinstance(cb_end, int):
        cytobands = list(filter(lambda d: int(d[ "start" ]) < cb_end, cytobands))

    return cytobands, chro, cb_start, cb_end

################################################################################

def _cytobands_label( cytobands ):

    cb_label = ""

    if len(cytobands) > 0:

        cb_label = cytobands[0]["chro"]+cytobands[0]["cytoband"]
        if len( cytobands ) > 1:
            cb_label = cb_label+cytobands[-1]["cytoband"]

    return cb_label

################################################################################


def _print_terminal_response(byc):

    if sys.stdin.isatty():
        if "error" in byc["service_response"]["response"]:
            if byc["service_response"]["response"][ "error" ][ "error_code" ] > 200:
                print( "\n"+byc["service_response"]["response"][ "error" ][ "error_message" ] )
                exit()

    if args.cytobands:
        print(str(byc["service_response"]["response"]["results"][0]["info"][ "chroBases" ]))
        exit()
    elif args.chrobases:
        print(str(byc["service_response"]["response"]["results"][0]["info"][ "cytoBands" ]))
        exit()

    return

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
