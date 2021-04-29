#!/usr/local/bin/python3

from os import path
from pymongo import MongoClient
import argparse, datetime
from isodate import date_isoformat

from lib.publication_utils import jprint, read_annotation_table, create_progenetix_post

"""
* pubUpdater.py -t 1 -f "../rsrc/publications.txt"
"""

##############################################################################
##############################################################################
##############################################################################

def _get_args():

    parser = argparse.ArgumentParser(description="Read publication annotations, create MongoDB posts and update the database.")
    parser.add_argument("-f", "--filepath", help="Path of the .tsv file containing the annotations on the publications.", type=str)
    parser.add_argument("-t", "--test", help="test setting")

    args = parser.parse_args()

    return args

##############################################################################

def main():
    update_publications()

##############################################################################

def update_publications():

    args = _get_args()

    if args.test:
        print( "¡¡¡ TEST MODE - no db update !!!")

    # Read annotation table:
    rows = read_annotation_table(args)

    print("=> {} publications will be looked up".format(len(rows)))

    # Connect to MongoDB and load publication collection
    client = MongoClient()
    cl = client['progenetix'].publications
    ids = cl.distinct("id")

    # Update the database
    for row in rows:

        post = create_progenetix_post(row)

        if post["id"] in ids:
            print(post["id"], ": skipped - already in progenetix.publications")

        else:
            print(post["id"], ": inserting this into progenetix.publications")

            post.update( { "updated": date_isoformat(datetime.datetime.now()) } )

            if not args.test:
                result = cl.insert_one(post)
                result.inserted_id
            else:
                jprint(post)

##############################################################################

if __name__ == '__main__':
        main()

##############################################################################
##############################################################################
##############################################################################
