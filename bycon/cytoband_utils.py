import csv
from os import path as path
import re

################################################################################
################################################################################
################################################################################

def parse_cytoband_file( **byc ):

    """podmd
 
    podmd"""

    cb_defs = byc["cytoband_defs"]["request_types"]["cytobands2chrobases"]

    # should be in a config but seems like overkill...
    # TODO: catch error for missing genome edition
    g_map = {
        "grch38": "grch38",
        "grch37": "hg19",
        "ncbi36": "hg18",
        "ncbi35": "hg17",
        "ncbi34": "hg16"
    }

    genome = byc["variant_pars"][ "assemblyId" ].lower()
    genome = re.sub( r"(\w+?)([^\w]\w+?)", r"\1", genome)

    if genome in g_map.keys():
        genome = g_map[ genome ]

    cb_file = path.join( byc[ "config" ][ "paths" ][ "genomes" ], genome, "CytoBandIdeo.txt" )
    cb_re = re.compile( cb_defs["parameters"][ "cytoBands" ][ "pattern" ] )

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

    return cytobands
