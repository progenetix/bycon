import csv
from os import path as path
from datetime import datetime, date
import time
import re, yaml
from isodate import parse_duration

################################################################################
################################################################################
################################################################################

def parse_cytoband_file( cb_file ):

    """podmd
 
    podmd"""

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

def subset_cytobands( cytobands, chro, cb_start, cb_end ):

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

