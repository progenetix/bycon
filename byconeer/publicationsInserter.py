#!/usr/local/bin/python3

from os import path, pardir
from pymongo import MongoClient
import argparse, datetime
from isodate import date_isoformat
import cgi, cgitb
import sys
import csv

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib import *

from lib.publication_utils import jprint, read_annotation_table, create_progenetix_post, create_short_publication_label, get_empty_publication, retrieve_epmc_publications

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

    rows = []

    mongo_client = MongoClient()

    pub_coll = mongo_client["progenetix"]["publications"]
    bios_coll = mongo_client["progenetix"]["biosamples"]

    publication_ids = pub_coll.distinct("id")

    progenetix_ids = bios_coll.distinct("external_references.id")
    progenetix_ids = [item for item in progenetix_ids if item is not None]
    progenetix_ids = list(filter(lambda x: x.startswith("PMID"), progenetix_ids))

    # TODO: Use schema ...

    with open(byc["args"].filepath, newline='') as csvfile:
        in_pubs = list(csv.DictReader(csvfile, delimiter="\t", quotechar='"'))
        print("=> {} publications will be looked up".format(len(in_pubs)))

        for pub in in_pubs:
            include = False
            if len(pub["pubmedid"]) > 5:
                pmid = pub["pubmedid"]
                p_k = "PMID:"+pmid

                """Publications are either created from an empty dummy or - if id exists and
                `-u 1` taken from the existing one."""

                if p_k in publication_ids:
                    if not byc["args"].update:
                        print(p_k, ": skipped - already in progenetix.publications")
                        continue
                    else:
                        n_p = mongo_client["progenetix"]["publications"].find_one({"id": p_k })
                        print(p_k, ": existed but overwritten since *update* in effect")
                else:
                    n_p = get_empty_publication()
                    n_p.update({"id":p_k})

                for k, v in pub.items():
                    if not k.startswith("_"):
                        # TODO: create dotted
                        assign_nested_value(n_p, k, v)

                if len(pub["_provenance_id"]) > 4:
                    geo_info = mongo_client["progenetix"]["geolocs"].find_one({"id": pub["_provenance_id"]}, {"_id": 0, "id": 0})
                    if geo_info is not None:
                        n_p["provenance"].update({"geo_location":geo_info})

                sts = {}

                pubmed_data = retrieve_epmc_publications(pmid)

                if pubmed_data is not None:
                    n_p.update({"abstract": re.sub(r'<[^\>]+?>', "", pubmed_data["abstractText"])})
                    n_p.update({"authors":pubmed_data["authorString"]})
                    n_p.update({"journal":pubmed_data["journalInfo"]["journal"]["medlineAbbreviation"]})
                    n_p.update({"title":re.sub(r'<[^\>]+?>', "", pubmed_data["title"])})
                    n_p.update({"year":pubmed_data["pubYear"]})
                
                n_p.update({"label": create_short_publication_label(n_p["authors"], n_p["title"], n_p["year"]) })

                if p_k in progenetix_ids:

                    n_p["counts"].update({"progenetix" : 0})

                    for s in bios_coll.find({ "external_references.id" : p_k }):
                        n_p["counts"]["progenetix"] += 1
                        h_d_id = s["histological_diagnosis"]
                        if "NCIT:C" in h_d_id["id"]:
                            if h_d in sts.keys():
                                sts[ h_d["id"] ][ "count" ] += 1
                            else:
                                sts.update( { h_d["id"]: h_d } )
                                sts[ h_d["id"] ].update({"count": 1})





                    



                jprint(n_p)
                    

    exit()

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

            if not byc["args"].test:
                result = cl.update_one({"id": post["id"] }, {"$set": post }, upsert=True )
                up_count += 1
            else:
                jprint(post)

    print("{} publications were inserted or updated".format(up_count))

##############################################################################
##############################################################################

if __name__ == '__main__':
        main()

##############################################################################
##############################################################################
##############################################################################
