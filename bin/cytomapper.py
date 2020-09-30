#!/usr/local/bin/python3

import cgi, cgitb
import re, yaml
from os import path as path
from sys import path as sys_path
import csv
import argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys_path.append(path.join(path.abspath(dir_path), '..'))
from bycon.parse_variants import *
from bycon.cgi_utils import *
from bycon.read_specs import *
from bycon.cytoband_utils import *


"""podmd

#### TODO

* fallback to info / documentation
* better error capture & documentation (e.g. wrong assemblies ...)
* warning about / correcting wrong cytoband syntax (e.g. *not* "17p11p12" *but* "17p12p11")
* species mapping from assembly id

podmd"""

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

    cytomapper("cytomapper")

################################################################################
################################################################################
################################################################################

def cytomapper(service):
    
    config = read_bycon_config( path.abspath( dir_path ) )
    config[ "paths" ][ "genomes" ] = path.join( config[ "paths" ][ "module_root" ], "rsrc", "genomes" )

    byc = {
        "config": config,
        "args": _get_args(),
        "cytoband_defs": read_named_prefs( "cytoband_definitions", dir_path ),
        "variant_defs": read_named_prefs( "variant_definitions", dir_path ),
        "form_data": cgi_parse_query(),
        "errors": [ ],
        "warnings": [ ]
    }

    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "cytobands": parse_cytoband_file( **byc ) } )

    # response prototype
    r = config["response_object_schema"]
    r.update( { "errors": byc["errors"], "warnings": byc["warnings"] } )
    r["response_type"] = service
    r["data"] = { }
    r["parameters"].update({ "assemblyId": byc["variant_pars"]["assemblyId"] })

    cytoBands = [ ]
    if "cytoBands" in byc["variant_pars"]:
        cytoBands, chro, start, end = _bands_from_cytobands( **byc )
        r["parameters"].update({ "cytoBands": byc["variant_pars"]["cytoBands"] })
    elif "chroBases" in byc["variant_pars"]:
        cytoBands, chro, start, end = _bands_from_chrobases( **byc )
        r["parameters"].update({ "chroBases": byc["variant_pars"]["chroBases"] })

    cb_label = _cytobands_label( cytoBands )

    r.update( { "parameters": byc["variant_pars"] } )
 
    if len( cytoBands ) < 1:
        r["errors"].append( "No matching cytobands!" )
        _print_terminal_response( byc["args"], r )
        _print_text_response( byc["form_data"], r )
        cgi_print_json_response( byc["form_data"], r, 422 )

    size = int(  end - start )
    chroBases = chro+":"+str(start)+"-"+str(end)
    
    r["data"].update( {
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
    } )

    # exception: only data response here... r was just for errors etc.

    _print_terminal_response( byc["args"], r )
    _print_text_response( byc["form_data"], r )
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################

def _bands_from_cytobands( **byc ):

    chr_bands = byc["variant_pars"]["cytoBands"]
    cb_pat = re.compile( byc["variant_defs"]["parameters"]["cytoBands"]["pattern"] )
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

def _bands_from_chrobases( **byc ):

    chr_bases = byc["variant_pars"]["chroBases"]
    cb_pat = re.compile( byc["variant_defs"]["parameters"]["chroBases"]["pattern"] )

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


def _print_terminal_response(args, r):

    if sys.stdin.isatty():
        if len(r[ "errors" ]) > 0:
            print( "\n".join( r[ "errors" ] ) )
            exit()

    if args.cytobands:
        print(str(r["data"]["info"][ "chroBases" ]))
        exit()
    elif args.chrobases:
        print(str(r["data"]["info"][ "cytoBands" ]))
        exit()

    return

################################################################################
################################################################################

def _print_text_response(form_data, r):

    if "text" in form_data:

        if "cytoBands" in r[ "parameters" ]:
            print('Content-Type: text')
            print()
            print(str(r["data"]["info"][ "chroBases" ])+"\n")
            exit()
        elif "chroBases" in r[ "parameters" ]:
            print('Content-Type: text')
            print()
            print(str(r["data"]["info"][ "cytoBands" ])+"\n")
            exit()

    return

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
