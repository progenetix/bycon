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
    parser.add_argument('-x', '--pgxuse', help='add entry for progenetix_use')    

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

    up_count = 0

    with open(byc["args"].filepath, newline='') as csvfile:

        in_pubs = list(csv.DictReader(csvfile, delimiter="\t", quotechar='"'))

        print("=> {} publications will be looked up".format(len(in_pubs)))

        for pub in in_pubs:

            if not "pubmedid" in pub:
                continue
            if "#" in pub:
                if len(pub["#"]) > 0:
                    print(pub["pubmedid"], ": skipped due to skip mark")
                    continue

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
                    n_p = get_empty_publication(byc)
                    n_p.update({"id":p_k})

                for k, v in pub.items():
                    if k:
                        if k[0].isalpha():
                            # TODO: create dotted
                            assign_nested_value(n_p, k, v)

                try:
                    if len(pub["#provenance_id"]) > 4:
                        geo_info = mongo_client["progenetix"]["geolocs"].find_one({"id": pub["#provenance_id"]}, {"_id": 0, "id": 0})
                        if geo_info is not None:
                            n_p["provenance"].update({"geo_location":geo_info["geo_location"]})
                except KeyError:
                    pass

                epmc = retrieve_epmc_publications(pmid)
                update_from_epmc_publication(n_p, epmc)            
                create_short_publication_label(n_p)
                get_ncit_tumor_types(n_p, pub)

                if p_k in progenetix_ids:

                    n_p["counts"].update({ "progenetix" : 0 })
                    n_p["counts"].update({ "arraymap" : 0 })

                    for s in bios_coll.find({ "external_references.id" : p_k }):
                        n_p["counts"]["progenetix"] += 1
                    for s in bios_coll.find({ "cohorts.id" : "pgxcohort-arraymap" }):
                        n_p["counts"]["arraymap"] += 1

                for c in n_p["counts"].keys():
                    if isinstance(n_p["counts"][c], str):
                        try:
                            n_p["counts"].update({c: int(n_p["counts"][c])})
                        except:
                            pass
                n_p["counts"]["ngs"] = n_p["counts"]["wes"] + n_p["counts"]["wgs"]

                if not byc["args"].test:
                    entry = pub_coll.update_one({"id": n_p["id"] }, {"$set": n_p }, upsert=True )
                    up_count += 1
                    print(n_p["id"]+": inserting this into progenetix.publications")
                else:
                    jprint(n_p)
                    
    print("{} publications were inserted or updated".format(up_count))

##############################################################################
##############################################################################



##############################################################################
##############################################################################

if __name__ == '__main__':
        main()

##############################################################################
##############################################################################
##############################################################################
