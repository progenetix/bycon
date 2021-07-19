#!/usr/local/bin/python3

from os import path, pardir
from pymongo import MongoClient
import argparse, datetime
from isodate import date_isoformat
import cgi, cgitb
import sys


# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib import *

from lib.publication_utils import jprint, read_annotation_table, create_progenetix_post

"""
* pubUpdater.py -t 1 -f "../rsrc/publications.txt"
"""

##############################################################################
##############################################################################
##############################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser(description="Read publication annotations, create MongoDB posts and update the database.")
    parser.add_argument("-f", "--filepath", help="Path of the .tsv file containing the annotations on the publications.", type=str)
    parser.add_argument("-t", "--test", help="test setting")
    parser.add_argument('-u', '--update', help='overwrite existing publications')

    byc.update({"args": parser.parse_args() })

    return byc

##############################################################################

def main():
    update_publications()

##############################################################################

def update_publications():

    byc = initialize_service()
    _get_args(byc)

    if byc["args"].test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    ##########################################
    # for Sofia => testing ... ###############
    ##########################################

    form_data = cgi.FieldStorage()
    new_pmid = form_data.getfirst("newPMID", "")
    if len(new_pmid) > 0:
        set_debug_state(1)
        print(new_pmid)
        exit()

    ##########################################
    ##########################################
    ##########################################

    # Read annotation table:
    rows = read_annotation_table(byc)

    print("=> {} publications will be looked up".format(len(rows)))

    # Connect to MongoDB and load publication collection
    client = MongoClient()
    cl = client['progenetix'].publications
    ids = cl.distinct("id")

    up_count = 0

    # Update the database
    for row in rows:

        post = create_progenetix_post(row, byc)

        if post:
            
            if post["id"] in ids:
                if not byc["args"].update:
                    print(post["id"], ": skipped - already in progenetix.publications")
                    continue
                else:
                    print(post["id"], ": existed but overwritten since *update* in effect")

            print(post["id"], ": inserting this into progenetix.publications")

            post.update( { "updated": date_isoformat(datetime.datetime.now()) } )

            if not byc["args"].test:
                result = cl.update_one({"id": post["id"] }, {"$set": post }, upsert=True )
                up_count += 1
            else:
                jprint(post)

    print("{} publications were inserted or updated".format(up_count))

##############################################################################

if __name__ == '__main__':
        main()

##############################################################################
##############################################################################
##############################################################################
