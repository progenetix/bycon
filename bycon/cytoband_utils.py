import csv
from os import path as path
import re, yaml

################################################################################
################################################################################
################################################################################

def parse_cytoband_file( **kwargs ):

    """podmd
 
    podmd"""

    genome = kwargs["variant_pars"][ "assemblyId" ].lower()
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

    if byc[ "variant_request_type" ] == "cytoband_mapping_request":
        cb_re = re.compile( byc["variant_defs"][ "cytoband" ][ "pattern" ] )
        chro, cb_start, cb_end = cb_re.match( byc["variant_pars"][ "cytoband" ] ).group(2, 3, 7)
        cytobands = _subset_cytobands_by_bands(  byc[ "cytobands" ], chro, cb_start, cb_end  )
    elif byc[ "variant_request_type" ] == "beacon_range_request":
        chro = byc["variant_pars"][ "referenceName" ]
        start = int( byc["variant_pars"][ "start" ] )
        end = int( byc["variant_pars"][ "end" ] )
        cytobands = _subset_cytobands_by_bases( cytobands, chro, start, end  )
    else:
        cytobands = [ ]
        chro = ""

    return(cytobands, chro)

################################################################################

def _subset_cytobands_by_bands( cytobands, chro, cb_start, cb_end ):

    if cb_start == None and cb_end == None:
        cytobands = list(filter(lambda d: d[ "chro" ] == chro, cytobands))
    else:
        cb_tmp = [ ]
        for cb in cytobands:
            if cb[ "chro" ] == chro:
                for cb_side in [ cb_start, cb_end ]:
                    if not cb_side == None:
                        cb_sre = re.compile( "^"+cb_side )
                        if cb_sre.match( cb[ "cytoband" ] ):
                           cb_tmp.append( cb )
        cytobands = cb_tmp

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
