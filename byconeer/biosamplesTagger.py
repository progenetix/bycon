#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
import statistics
from progress.bar import Bar
import csv


# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_sub = path.dirname(__file__)
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib import *

"""

## `biosamplesRefresher`

"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-t", "--test", help="test setting")
    parser.add_argument('-i', '--inputfile', help='accustom file  to specify input data')
    parser.add_argument('-m', '--mode', help='update modus')
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    biosamples_tagger()

################################################################################

def biosamples_tagger():

    byc = initialize_service()
    _get_args(byc)

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    select_dataset_ids(byc)
    check_dataset_ids(byc)
    parse_filters(byc)
    parse_variants(byc)
    initialize_beacon_queries(byc)

    generate_genomic_intervals(byc)

    if len(byc["dataset_ids"]) != 1:
        print("No single, existing dataset was provided with -d ...")
        exit()

    ds_id = byc["dataset_ids"][0]

    if not byc["args"].mode:
        print("No update modus specified => quitting ...")
        exit()
    if not byc["args"].inputfile:
        print("No inputfile file specified => quitting ...")
        exit()

    # TODO: Move  to sub ...
    i_t = []
    f_p = byc["args"].inputfile
    with open(f_p) as f:
       rd = csv.reader(f, delimiter="\t", quotechar='"')
       for i, row in enumerate(rd):
           if i > 0:
               i_t.append(row)


    row_no = len(i_t)

    not_found = []

    data_client = MongoClient( )
    bios_coll = data_client[ ds_id ][ "biosamples" ]

    if byc["args"].mode == "cohorttag":

        cohort = {
            "id": "pgxcohort-carriocordo2021heterogeneity",
            "label": "Carrio-Cordo and Baudis - Genomic Heterogeneity in Cancer Types (2021)"
        }
 
        bar = Bar("Reading in metadata table", max = row_no, suffix="%(percent)d%%"+" of "+str(row_no) )
        for row in i_t:
            if row[0].startswith('#'):
                continue

            bs = bios_coll.find_one({"info.legacy_id":row[0]})

            if not bs:
                not_found.append(row[0])
                bar.next()
                continue

            bios_coll.update_one(
                {"info.legacy_id":row[0]},
                {"$addToSet": { "cohorts": cohort} }
            )

            bar.next()
        bar.finish()

        print(" biosamples could not be found and tagged".format(len(not_found)))

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
