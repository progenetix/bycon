#!/usr/local/bin/python3

import sys, yaml, re, json
from pymongo import MongoClient
from os import path as path

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *
from pgy import *

################################################################################
################################################################################
################################################################################

def main():

    """podmd

    This app starts out by creating the "old style" tab-indented tree file from
    Protégé C&P Neoplasn Core exports (file for labels, file for codes).

    #### Source:

    * <http://www.obofoundry.org/ontology/ncit.html>

    end_podmd"""

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "ncit" ] = path.join( config[ "paths" ][ "module_root" ], "rsrc", "ncit" )

    ncit_p = config[ "paths" ][ "ncit" ]

    labels_f = path.join( ncit_p, "ncit-neoplasm-tree-labels.txt" )
    codes_f = path.join( ncit_p, "ncit-neoplasm-tree-codes.txt" )
    hierarchies_out = path.join( ncit_p, "hierarchies.tsv" )
    labels_out = path.join( ncit_p, "labels.tsv" )

    l_d = { }

    f = open(labels_f, 'r+')
    labels = [line for line in f.readlines()]
    f.close()
    f = open(codes_f, 'r+')
    codes = [line for line in f.readlines()]
    f.close()

    h_f = open( hierarchies_out, 'w' )
    i = 0
    for c_l in codes:
        c_l = c_l.rstrip()
        c_l = c_l.replace("obo:NCIT_", "NCIT:")
        c = re.sub(r"\s+", "", c_l)
        l = labels[ i ].strip()
        c_l = c_l.replace("NCIT", l+" (NCIT") + ")"

        h_f.write( c_l + "\n")
        l_d.update( { c: l } )

        i += 1

    h_f.close()

    l_f = open( labels_out, 'w' )
    for c, l in l_d.items():
        l_f.write( "{}\t{}\n".format(c, l) )
    l_f.close()

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
