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

* a "Beacon-style" positional request (`assemblyId`, `referenceName`, `start`, `end`), to retrieve
overlapping cytobands, or
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

* using the new [ChromosomeLocation](https://vr-spec.readthedocs.io/en/181-chromosomelocation/terms_and_model.html#chromosomelocation) object:
  - <https://progenetix.org/cgi/bycon/bin/cytomapper.py?type=ChromosomeLocation&assemblyId=GRCh38&chr=17&start=p11&end=q21>
* retrieve coordinates for some bands on chromosome 8
  - <https://progenetix.org/cgi/bycon/bin/cytomapper.py?assemblyId=NCBI36.1&cytoBands=8q>
* as above, just as text:
  - <https://progenetix.org/cgi/bycon/bin/cytomapper.py?assemblyId=NCBI.1&cytoBands=8q&text=1>
  - *cytomapper shortcut*: <https://progenetix.org/services/cytomapper/?assemblyId=NCBI36.1&cytoBands=8q&text=1>
* get the cytobands whith which a base range on chromosome 17 overlaps, in short and long form
  - <https://progenetix.org/cgi/bycon/bin/cytomapper.py?assemblyId=GRCh38&referenceName=17&start=800000&end=24326000>
  - <https://progenetix.org/cgi/bycon/bin/cytomapper.py?assemblyId=NCBI36&chroBases=17:800000-24326000>
* using `curl` to get the text format mapping of a cytoband range, using the API `services` shortcut:
  - `curl -k https://progenetix.org/services/cytomapper/cytoBands\=8q21q24.1/assemblyId\=hg18/text\=1/`
* command line version of the above
  - `bin/cytomapper.py --chrobases 17:800000-24326000 -g NCBI36`
  - `bin/cytomapper.py -b 17:800000-24326000`
  - `bin/cytomapper.py --cytobands 9p11q21 -g GRCh38`
  - `bin/cytomapper.py -c Xpterq24`

#### TODO

* fallback to info / documentation
* better error capture & documentation (e.g. wrong assemblies ...)
* warning about / correcting wrong cytoband syntax (e.g. *not* "17p11p12" *but* "17p12p11")

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

    return(args)

################################################################################

def main():

    cytomapper()

################################################################################
################################################################################
################################################################################

def cytomapper():
    
    # input & definitions
    form_data = cgi_parse_query()
    args = _get_args()
    rest_pars = cgi_parse_path_params( "cytomapper" )

    if "debug" in form_data:
        cgitb.enable()
        print('Content-Type: text')
        print()
    else:
        pass

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( *config[ "paths" ][ "web_temp_dir_abs" ] )
    config[ "paths" ][ "genomes" ] = path.join( config[ "paths" ][ "module_root" ], "rsrc", "genomes" )

    byc = {
        "config": config,
        "args": args,
        "cytoband_defs": read_cytoband_definitions( **config[ "paths" ] ),
        "form_data": form_data,
        "rest_pars": rest_pars
    }

    byc.update( { "cytoband_pars": _parse_cytobands( **byc ) } )
    byc.update( { "cytoband_request_type": _get_cytoband_request_type( **byc ) } )
    byc.update( { "cytobands": parse_cytoband_file( **byc ) } )
    cytoBands, chro, cb_label = filter_cytobands( **byc )

    # response prototype
    cyto_response = { "request": byc["cytoband_pars"], "error": None }

    if len( cytoBands ) < 1:
        cyto_response.update( { "error": "No matching cytobands!" } )
        _print_terminal_response(args, cyto_response)
        _print_text_response(form_data, rest_pars, cyto_response)
        cgi_print_json_response(cyto_response)
    start = int( cytoBands[0]["start"] )
    end = int( cytoBands[-1]["end"] )
    if byc[ "cytoband_request_type" ] == "positions2cytobands":
        start = int( byc["cytoband_pars"][ "start" ] )
        end = int( byc["cytoband_pars"][ "end" ] )

    size = int(  end - start )
    chroBases = chro+":"+str(start)+"-"+str(end)
    
    cyto_response.update( {
        "assemblyId": byc["cytoband_pars"][ "assemblyId" ],
        "cytoBands": cb_label,
        "chroBases": chroBases,
        "referenceName": chro,
        "start": start,
        "end": end,
        "size": size,
        "ChromosomeLocation": {
            "type": "ChromosomeLocation",
            "chr": chro,
            "start": cytoBands[0]["cytoband"],
            "end": cytoBands[-1]["cytoband"]
        }
    } )

    _print_terminal_response(args, cyto_response)
    _print_text_response(form_data, rest_pars, cyto_response)

    if "callback" in byc[ "form_data" ]:
        cgi_print_json_callback(byc["form_data"].getvalue("callback"), [cyto_response])
    else:
        cgi_print_json_response(cyto_response)

################################################################################
################################################################################


def _parse_cytobands( **byc ):

    cb_pars = { }
    v_p_defs = byc["cytoband_defs"]["parameters"]
    args = byc["args"]

    for p_k in v_p_defs.keys():
        v_default = None
        if "default" in v_p_defs[ p_k ]:
            v_default = v_p_defs[ p_k ][ "default" ]
        if "array" in v_p_defs[ p_k ]["type"]:
            cb_pars[ p_k ] = byc["form_data"].getlist(p_k)
        else:
            cb_pars[ p_k ] = byc["form_data"].getvalue(p_k, v_default)
        if not cb_pars[ p_k ]:
            del( cb_pars[ p_k ] )
        # except Exception:
        #     pass

    # for debugging
    args = byc["args"]
    if "test" in args:
        if args.test:
            cb_pars = byc["service_info"][ "sampleAlleleRequests" ][0]
    if "cytobands" in args:
        if args.cytobands:
            cb_pars[ "cytoBands" ] = args.cytobands
    if "chrobases" in args:
        if args.chrobases:
            cb_pars[ "chroBases" ] = args.chrobases
    if "genome" in args:
        if args.genome:
            cb_pars[ "assemblyId" ] = args.genome

    # TODO: rest_pars shouldn't be used anymore; still for cytomapper...
    if "rest_pars" in byc:
        for rp in byc[ "rest_pars" ].keys():
            if rp in v_p_defs:
                cb_pars[ rp ] = byc[ "rest_pars" ][ rp ]

    # value checks
    # TODO: a bit hacky; reduced from the systematic variant parsing ...
    v_p_c = { }

    if "type" in cb_pars:
        if cb_pars[ "type" ] == "ChromosomeLocation":
            if "chr" in cb_pars:
                cb_pars["cytoBands"] = cb_pars["chr"]+cb_pars["start"]+cb_pars["end"]
                del(cb_pars["start"])
                del(cb_pars["end"])

    for p_k in cb_pars.keys():
        if not p_k in v_p_defs.keys():
            continue
        v_p = cb_pars[ p_k ]

        if re.compile( v_p_defs[ p_k ][ "pattern" ] ).match( str( v_p ) ):
            if "integer" in v_p_defs[ p_k ][ "type" ]:
                v_p = int( v_p )
            v_p_c[ p_k ] = v_p

    v_par = "chroBases"
    if v_par in cb_pars:
        cb_re = re.compile( v_p_defs[ v_par ][ "pattern" ] )
        chro, start, end = cb_re.match( v_p_c[ v_par ] ).group(2, 3, 5)
        if not end:
            end = int(start) + 1
        v_p_c[ "referenceName" ] = chro
        v_p_c[ "start" ] = int(start)
        v_p_c[ "end" ] = int(end)

    if "chr" in v_p_c:
        v_p_c["referenceName"] = v_p_c[ "chr" ]

    return v_p_c


################################################################################

def _get_cytoband_request_type( **byc ):
    
    cb_request_type = "no correct variant request"

    c_pars = byc["cytoband_pars"]
    c_defs = byc["cytoband_defs"]
    r_types = c_defs["request_types"]

    if not c_pars["assemblyId"]:
        return cb_request_type

    if "cytoBands" in c_pars:
        return "cytobands2positions"

    if "type" in c_pars:
        if c_pars["type"] == "ChromosomeLocation":
            return "cytobands2positions"

    if "referenceName" in c_pars:
        return "positions2cytobands"

    return cb_request_type

################################################################################
################################################################################

def _print_terminal_response(args, cyto_response):

    if not args is None:
        if not cyto_response[ "error" ] is None:
            print( cyto_response[ "error" ] )
            exit()

    if args.cytobands:
        print(str(cyto_response[ "chroBases" ]))
        exit()
    elif args.chrobases:
        print(str(cyto_response[ "cytoBands" ]))
        exit()

    return

################################################################################
################################################################################

def _print_text_response(form_data, rest_pars, cyto_response):

    if "text" in form_data or "text" in rest_pars:

        if "cytoBands" in cyto_response[ "request" ]:
            print('Content-Type: text')
            print()
            print(str(cyto_response[ "chroBases" ])+"\n")
            exit()
        elif "chroBases" in cyto_response[ "request" ]:
            print('Content-Type: text')
            print()
            print(str(cyto_response[ "cytoBands" ])+"\n")
            exit()

    return

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
