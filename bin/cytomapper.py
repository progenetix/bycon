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
from bycon.beacon_parse_variants import *
from bycon.cgi_utils import *
from bycon.beacon_process_specs import *
from bycon.cytoband_utils import *


"""podmd

This script parses either:

* a properly formatted cytoband annotation (`assemblyId`, `cytoBands`)
  - "8", "9p11q21", "8q", "1p12qter"
* a concatenated `chroBases` parameter
  - `7:23028447-45000000`
  - `X:99202660`

While the return object is JSON by default, specifying `text=1`, together with the `cytoBands` or
`chroBases` parameter will return the text version of the opposite.

There is a fallback to *GRCh38* if no assembly is being provided.

The `cytobands` and `chrobases` parameters can be used for running the script on the command line
(see examples below). Please be aware of the "chrobases" (command line) versus "chroBases" (cgi) use.

#### Examples

* retrieve coordinates for some bands on chromosome 8
  - <https://progenetix.org/services/cytomapper?assemblyId=NCBI36.1&cytoBands=8q>
* as above, just as text:
  - <https://progenetix.org/services/cytomapper?assemblyId=NCBI.1&cytoBands=8q&text=1>
  - *cytomapper shortcut*: <https://progenetix.org/services/cytomapper/?assemblyId=NCBI36.1&cytoBands=8q&text=1>
* get the cytobands whith which a base range on chromosome 17 overlaps, in short and long form
  - <https://progenetix.org/services/cytomapper?assemblyId=NCBI36&chroBases=17:800000-24326000>
* using `curl` to get the text format mapping of a cytoband range, using the API `services` shortcut:
  - `curl -k https://progenetix.org/services/cytomapper?cytoBands\=8q21q24.1&assemblyId\=hg18&text\=1`
* command line version of the above
  - `bin/cytomapper.py --chrobases 17:800000-24326000 -g NCBI36`
  - `bin/cytomapper.py -b 17:800000-24326000`
  - `bin/cytomapper.py --cytobands 9p11q21 -g GRCh38`
  - `bin/cytomapper.py -c Xpterq24`

#### Response

```
{
    "data": {
        "ChromosomeLocation": {
            "chr": "7",
            "end": "q21.12",
            "species": "",
            "start": "p21.3",
            "type": "ChromosomeLocation"
        },
        "assemblyId": "GRCh38",
        "bandList": [
            "7p21.3",
            "7p21.2",
            "7p21.1",
            "7p15.3",
            "7p15.2",
            "7p15.1",
            "7p14.3",
            "7p14.2",
            "7p14.1",
            "7p13",
            "7p12.3",
            "7p12.2",
            "7p12.1",
            "7p11.2",
            "7p11.1",
            "7q11.1",
            "7q11.21",
            "7q11.22",
            "7q11.23",
            "7q21.11",
            "7q21.12"
        ],
        "chroBases": "7:7200000-88500000",
        "cytoBands": "7p21.3q21.12",
        "end": 88500000,
        "referenceName": "7",
        "size": 81300000,
        "start": 7200000
    },
    "errors": [],
    "parameters": {
        "assemblyId": "GRCh38",
        "chroBases": "7:12000000-88000000"
    },
    "warnings": []
}
```

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
        "cytoband_defs": read_yaml_to_object( "cytoband_definitions_file", **config[ "paths" ] ),
        "variant_defs": read_yaml_to_object( "variant_definitions_file", **config[ "paths" ] ),
        "form_data": cgi_parse_query(),
        "error": { }
    }

    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "cytobands": parse_cytoband_file( **byc ) } )

    # response prototype
    r = config["response_object_schema"]

    cytoBands = [ ]

    if "cytoBands" in byc["variant_pars"]:
        cytoBands, chro = _bands_from_cytobands( **byc )
    elif "chroBases" in byc["variant_pars"]:
        cytoBands, chro = _bands_from_chrobases( **byc )

    cb_label = _cytobands_label( cytoBands )

    r.update( { "parameters": byc["variant_pars"] } )
    if byc["error"]:
        r["errors"].append( byc["error"] )

    if len( cytoBands ) < 1:
        r["errors"].append( "No matching cytobands!" )
        _print_terminal_response( byc["args"], r )
        _print_text_response( byc["form_data"], r )
        cgi_print_json_response( byc["form_data"], r )

    start = int( cytoBands[0]["start"] )
    end = int( cytoBands[-1]["end"] )
    size = int(  end - start )
    chroBases = chro+":"+str(start)+"-"+str(end)
    
    r["data"].update( {
        "assemblyId": byc["variant_pars"][ "assemblyId" ],
        "cytoBands": cb_label,
        "bandList": [x['chroband'] for x in cytoBands ],
        "chroBases": chroBases,
        "referenceName": chro,
        "start": start,
        "end": end,
        "size": size,
        "ChromosomeLocation": {
            "type": "ChromosomeLocation",
            "species": "",
            "chr": chro,
            "start": cytoBands[0]["cytoband"],
            "end": cytoBands[-1]["cytoband"]
        }
    } )

    _print_terminal_response( byc["args"], r )
    _print_text_response( byc["form_data"], r )
    cgi_print_json_response( byc["form_data"], r )

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

    return cytobands, chro

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
    if cb_start == None and cb_end == None:
        return cytobands, chro

    if isinstance(cb_start, int):
        cytobands = list(filter(lambda d: int(d[ "end" ]) > cb_start, cytobands))

    if isinstance(cb_end, int):
        cytobands = list(filter(lambda d: int(d[ "start" ]) < cb_end, cytobands))

    return cytobands, chro

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
        print(str(r["data"][ "chroBases" ]))
        exit()
    elif args.chrobases:
        print(str(r["data"][ "cytoBands" ]))
        exit()

    return

################################################################################
################################################################################

def _print_text_response(form_data, r):

    if "text" in form_data:

        if "cytoBands" in r[ "parameters" ]:
            print('Content-Type: text')
            print()
            print(str(r["data"][ "chroBases" ])+"\n")
            exit()
        elif "chroBases" in r[ "parameters" ]:
            print('Content-Type: text')
            print()
            print(str(r["data"][ "cytoBands" ])+"\n")
            exit()

    return

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
