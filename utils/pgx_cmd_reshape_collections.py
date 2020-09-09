#!/usr/local/bin/python3

import re, yaml, json
from os import path as path
from os import system
from sys import path as sys_path
from pymongo import MongoClient
from datetime import datetime, date
from progress.bar import IncrementalBar
import argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys_path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--datasetid", help="dataset")
    parser.add_argument("-a", "--alldatasets", action='store_true', help="process all datasets")
    parser.add_argument("-t", "--test", help="test setting")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )

    args = _get_args()

    if args.alldatasets:
        dataset_ids = config[ "dataset_ids" ]
    else:
        dataset_ids =  [ args.datasetid ]
        if not dataset_ids[0] in config[ "dataset_ids" ]:
            print("No existing dataset was provided with -d ...")
            exit()

    """podmd
    The `"mongostring": True` setting leads to the query being prepared as
    _MongoDB_ string literal, instead of a dictionary for `pymongo` use.
    podmd"""

    kwargs = {
        "config": config,
        "args": args,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ) 
    }

    for ds_id in dataset_ids:
        _process_reshaping_commands(ds_id, **kwargs)

################################################################################

def _process_reshaping_commands(ds_id, **kwargs):

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ ds_id ]
    bios_coll = mongo_db[ "biosamples" ]   
    cs_coll = mongo_db[ "callsets" ]

    bar = IncrementalBar(ds_id+' samples', max = bios_coll.estimated_document_count() )

    for bios in bios_coll.find( { } ):
        update = bios.copy()

        # recurring modifications / updates ####################################
        
        if "info" in update:
            u_i = { }
            for i_k, i_v in update["info"].items():
                if i_v:
                    u_i.update( { i_k: i_v } )
            update.update( { "info": u_i } )

        cs_ids = [ ]
        for cs in cs_coll.find( { "biosample_id": bios["id"] } ):
            cs_ids.append(cs["id"])
        if len(cs_ids) > 0:
            if not "info" in update:
                update.update( { "info": { } } ) 
            update["info"].update( { "callset_ids": cs_ids } )

        # one time modifications; to be purged / modified ######################

        if "age_at_collection" in update:
            if update["age_at_collection"]["age"]:
                update.update( { "individual_age_at_collection": update["age_at_collection"]["age"] } )
            del update["age_at_collection"]

        if "geo_provenance" in update:
            del update["geo_provenance"]
        if "project_id" in update:
            del update["project_id"]

        u_b = [ ]
        for b in update["biocharacteristics"]:
            if "description" in b:
                del b["description"]
            u_b.append(b)
        update.update( { "biocharacteristics": u_b } )

        u_e = [ ]
        for e in update["external_references"]:
            if "relation" in e["type"]:
                e["type"].pop("relation")
            u_e.append(e)
        update.update( { "external_references": u_e } )

        # update itself ########################################################

        update.update( { "updated": datetime.now() } )

        if kwargs[ "args"].test:
            print( json.dumps(update, indent=4, sort_keys=True, default=str) )
        else:
            bios_coll.replace_one( { "_id" : bios[ "_id" ] }, update )

        bar.next()
    bar.finish()
    

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main(  )
