#!/usr/local/bin/python3
from pymongo import MongoClient
from os import path, environ, pardir
import sys, datetime
from progress.bar import Bar

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_sub = path.dirname(__file__)
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer.lib import *

################################################################################

def _get_args(byc):

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetids", help="datasets, comma-separated")
    byc.update({ "args": parser.parse_args() })

    return byc

################################################################################
def main():

    callsets_modifier()

################################################################################

def callsets_modifier():

    byc = initialize_service()
    _get_args(byc)

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    if len(byc["dataset_ids"]) < 1:
        print("No existing dataset was provided with -d ...")
        exit()

	############################################################################

    for ds_id in byc["config"]["dataset_ids"]:

	    data_client = MongoClient( )
	    data_db = data_client[ ds_id ]
	    cs_coll = data_db[ "callsets" ]
	    bios_coll = data_db[ "biosamples" ]

	    cs_no = cs_coll.estimated_document_count()
	    bar = Bar("{} callsets from {}".format(cs_no, ds_id), max = cs_no, suffix='%(percent)d%%'+" of "+str(cs_no) )

	    for cs in cs_coll.find({}):

	    	bar.next()

	    	bios_id = cs["biosample_id"]
	    	bios = bios_coll.find_one({"id": bios_id })

	    	try:
	    		cs_coll.update_one({"_id": cs["_id"]}, {"$set": {"individual_id": bios["individual_id"]}})
	    	except:
	    		print(bios)

	    bar.finish()

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
