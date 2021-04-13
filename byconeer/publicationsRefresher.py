#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
import argparse
import statistics
from progress.bar import Bar

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_sub = path.dirname(__file__)
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib.read_specs import *
from beaconServer.lib.parse_filters import *
from beaconServer.lib.service_utils import initialize_service
from beaconServer.lib.schemas_parser import *

# from lib.publication_parser import * # TODO ...

"""

## `publicationsRefresher`

"""

################################################################################
################################################################################
################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", help="test setting")
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################

def main():

    publications_refresher()

################################################################################

def publications_refresher():

    byc = initialize_service()
    _get_args(byc)

    test_mode = False
    if byc["args"].test:
        test_mode = 1

################################################################################

    # test_mode is for dry runs, e.g. to print out test values w/o data updates
    if test_mode:
        print( "¡¡¡ TEST MODE - no db update !!!")

    data_client = MongoClient( )
    data_db = data_client[ "progenetix" ]
    pub_coll = data_db[ "publications" ]
    bios_coll = data_db[ "biosamples" ]

    no =  pub_coll.estimated_document_count()

    if not test_mode:
        bar = Bar("Refreshing publications", max = no, suffix='%(percent)d%%'+" of "+str(no) )

    for p in pub_coll.find({}):

        update_obj = { "sample_types": [ ] }
        update_flag = False
        sts = {}

        for s in bios_coll.find({ "external_references.id" : p["id"] }):
            if "biocharacteristics" in s:
                for b_c in s[ "biocharacteristics" ]:
                     if "NCIT:C" in b_c["id"]:
                        if b_c["id"] in sts:
                            sts[ b_c["id"] ][ "count" ] += 1
                        else:
                            sts.update( { b_c["id"]: b_c } )
                            sts[ b_c["id"] ][ "count" ] = 1

        if sts.keys():
            update_flag = 1
            for k, st in sts.items():
                update_obj["sample_types"].append(st)

        if not test_mode:
            if update_flag:
                pub_coll.update_one( { "_id": p["_id"] }, { '$set': update_obj }  )
            bar.next()
 
    if not test_mode:
        bar.finish()

################################################################################
################################################################################
################################################################################


if __name__ == '__main__':
    main()
