import csv
from os import path as path
import re

from os import path, pardir
import inspect, json
from pymongo import MongoClient
from bson import json_util

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

    chromosomes = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,"X","Y"]

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

    # making sure the chromosomes are sorted!
    for chro in chromosomes:
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

################################################################################

def generate_genomic_intervals(byc, int_type="bins", int_size=1000000):

    if not "cytobands" in byc:
        parse_cytoband_file(byc)

    chro_maxes = {}
    for cb in byc["cytobands"]:               # assumes the bands are sorted
        chro_maxes.update({ cb["chro"]: int(cb["end"])})

    byc["genomic_intervals"] = []
    i = 0

    if int_type == "cytobands":
        for cb in byc["cytobands"]:
            byc["genomic_intervals"].append( {
                    "index": int(cb["i"]),
                    "chro": cb["chro"],
                    "start": int(cb["start"]),
                    "end": int(cb["end"]),
                    "size": int(cb["end"]) - int(cb[ "start"])
                })
        return byc

    # otherwise intervals

    for chro in chro_maxes:
        start = 0
        end = start + int_size
        while start <= chro_maxes[chro]:
            if end > chro_maxes[chro]:
                end = chro_maxes[chro]
            byc["genomic_intervals"].append( {
                    "index": i,
                    "chro": chro,
                    "start": start,
                    "end": end,
                    "size": end - start
                })
            start += int_size
            end += int_size
            i += 1

    return byc
