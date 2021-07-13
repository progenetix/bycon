#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
import argparse

################################################################################
################################################################################
################################################################################

"""
./ontologyTermLister.py -c rsrc/NCITstage/NCITstage-codes.tsv -l rsrc/NCITstage/NCITstage-labels.tsv -o rsrc/NCITstage/numbered-hierarchies.tsv
"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--codefile", help="")
    parser.add_argument("-l", "--labelfile",help="")
    parser.add_argument("-o", "--hierarchyfile", help="")
   
    return parser.parse_args()

################################################################################

def main():

    args = _get_args()

    codes_f = args.codefile
    labels_f = args.labelfile
    hierarchy_f = args.hierarchyfile

    f = open(labels_f, 'r+')
    labels = [line for line in f.readlines()]
    f.close()
    f = open(codes_f, 'r+')
    codes = [line for line in f.readlines()]
    f.close()

    n_h_f = open( hierarchy_f, 'w' )

    i = 0
    for c_l in codes:
        c_l = c_l.rstrip()
        c_l = c_l.replace("obo:NCIT", "NCIT")
        c_l = c_l.replace("_", ":")
        tab_n = c_l.count("\t")
        c = re.sub(r"\s+", "", c_l)
        l = labels[ i ].strip()

        # c_l = c_l.replace("NCIT", l+" (NCIT") + ")"
        # h_f.write( c_l + "\n")
        # l_d.update( { c: l } )

        i += 1

        n_h_f.write( "{}\t{}\t{}\t{}\n".format(c, l, tab_n, i) )

    n_h_f.close()

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
