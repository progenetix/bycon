import csv
import re
from os import path, pardir

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )

################################################################################
################################################################################
################################################################################

def parse_cytoband_file(byc):

    """podmd
 
    podmd"""
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

    cb_file = path.join( pkg_path, "services", "rsrc", "genomes", genome, "CytoBandIdeo.txt" )
    
    cb_re = re.compile( byc["interval_definitions"][ "cytobands" ][ "pattern" ] )

    cb_keys = [ "chro", "start", "end", "cytoband", "staining" ]
    cytobands = [ ]
    i = 0

    c_bands = [ ]
    with open(cb_file) as cb_f:                                                                                          
        for c_band in csv.DictReader(filter(lambda row: row[0]!='#', cb_f), fieldnames=cb_keys, delimiter='\t'):
            c_bands.append(c_band)

    # !!! making sure the chromosomes are sorted !!!
    for chro in byc["interval_definitions"][ "chromosomes" ]:
        c_m = "chr"+str(chro)
        for cb in c_bands:
            if cb[ "chro" ] == c_m:
                cb[ "i" ] = i
                cb[ "chro" ] = cb[ "chro" ].replace( "chr", "")
                cb[ "chroband" ] = cb[ "chro" ]+cb[ "cytoband" ]
                cytobands.append(dict(cb))
                i += 1
    
    byc.update( { "cytobands": cytobands } )

    return byc

