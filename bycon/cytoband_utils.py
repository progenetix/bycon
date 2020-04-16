import csv
from os import path as path
import re, yaml

################################################################################
################################################################################
################################################################################

def parse_cytoband_file( **kwargs ):

    """podmd
 
    podmd"""

    # should be in a config but seems like overkill...
    # TODO: catch error for missing genome edition
    g_map = {
        "grch38": "grch38",
        "grch37": "hg19",
        "ncbi36": "hg18",
        "ncbi35": "hg17",
        "grch34": "hg16"
    }

    genome = kwargs["variant_pars"][ "assemblyId" ].lower()
    genome = re.sub( r"(\w+?)([^\w]\w+?)", r"\1", genome)

    if genome in g_map.keys():
        genome = g_map[ genome ]

    cb_file = path.join( kwargs[ "config" ][ "paths" ][ "genomes" ], genome, "CytoBandIdeo.txt" )
    cb_re = re.compile( kwargs["variant_defs"][ "cytoband" ][ "pattern" ] )

    cb_keys = [ "chro", "start", "end", "cytoband", "staining" ]
    cytobands = [ ]
    cb_no = 0

    with open(cb_file) as cb_f:                                                                                          
        cb_reader = csv.DictReader(filter(lambda row: row[0]!='#', cb_f), fieldnames=cb_keys, delimiter='\t')
        for cb in cb_reader:
            cb_no += 1
            cb[ "i" ] = cb_no
            cb[ "chro" ] = cb[ "chro" ].replace( "chr", "")
            cb[ "chroband" ] = cb[ "chro" ]+cb[ "cytoband" ]
            cytobands.append(dict(cb))

    return(cytobands)

################################################################################

def filter_cytobands( **byc ):

    if byc[ "variant_request_type" ] == "cytobands2positions_request":
        cb_re = re.compile( byc["variant_defs"][ "cytoband" ][ "pattern" ] )
        chro, cb_start, cb_end = cb_re.match( byc["variant_pars"][ "cytoband" ] ).group(2, 3, 9)
        cytobands = _subset_cytobands_by_bands(  byc[ "cytobands" ], chro, cb_start, cb_end  )
        cb_label = _cytobands_label( cytobands )
    elif byc[ "variant_request_type" ] == "positions2cytobands_request":
        chro = byc["variant_pars"][ "referenceName" ]
        start = int( byc["variant_pars"][ "start" ] )
        end = int( byc["variant_pars"][ "end" ] )
        cytobands = _subset_cytobands_by_bases( byc[ "cytobands" ], chro, start, end  )
        cb_label = _cytobands_label( cytobands )
    else:
        cytobands = [ ]
        chro = ""
        cb_label = ""

    return(cytobands, chro, cb_label)

################################################################################

def _cytobands_label( cytobands ):

    cb_label = cytobands[0]["chro"]+cytobands[0]["cytoband"]
    if len( cytobands ) > 1:
        cb_label = cb_label+cytobands[-1]["cytoband"]

    return(cb_label)

################################################################################

def _subset_cytobands_by_bands( cytobands, chro, cb_start, cb_end ):

    cytobands = list(filter(lambda d: d[ "chro" ] == chro, cytobands))

    if cb_start == None and cb_end == None:
        return( cytobands )
    else:

        cb_from = 0
        cb_to = len(cytobands)

        if cb_start == None or cb_start == "pter":
            cb_start = "p"
        if cb_end == None or cb_end == "qter":
            cb_end = "q"
        cb_s_re = re.compile( "^"+cb_start )
        cb_e_re = re.compile( "^"+cb_end )
        i = 0

        # searching for the first matching band
        for cb in cytobands:
            if cb_s_re.match( cb[ "cytoband" ] ):
                cb_from = i
                break
            i += 1
        k = 0

        # retrieving the last matching band
        # => index at least as start to avoid "q21qter" => "all q"
        for cb in cytobands:
            if k >= i:
                if cb_e_re.match( cb[ "cytoband" ] ):
                    cb_to = k+1
            k += 1

        cytobands = cytobands[cb_from:cb_to]

    return( cytobands )

################################################################################

def _subset_cytobands_by_bases( cytobands, chro, start, end ):

    cytobands = list(filter(lambda d: d[ "chro" ] == chro, cytobands))
    if isinstance(start, int):
        cytobands = list(filter(lambda d: int(d[ "end" ]) > start, cytobands))

    if isinstance(end, int):
        cytobands = list(filter(lambda d: int(d[ "start" ]) < end, cytobands))

    return( cytobands )

################################################################################
