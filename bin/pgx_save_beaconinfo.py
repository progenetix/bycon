#!/usr/local/bin/python3

import re, json, yaml
from os import path as path
from os import environ
import sys, os, datetime
from isodate import date_isoformat
from pymongo import MongoClient
from progress.bar import Bar

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""

This script reads the Beacon definitions from the configuration files, populates
the filter definition and dataset statistics and saves the information ino the
`progenetix.beaconinfo` database, from where it can be used e.g. by the Beacon
API (`byconplus`).

"""

################################################################################
################################################################################
################################################################################

def main():
    
    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    bsif = path.join( config[ "paths" ][ "module_root" ], *config[ "paths" ][ "service_info_file" ] )

    # input & definitions

    byc = {
        "config": config,
        "get_filters": True,
    }

    byc.update( { "filter_defs": read_filter_definitions( **byc ) } )
    byc.update( { "datasets_info": read_datasets_info( **byc ) } )

    ds_with_counts = [ ]

    print("=> updating entry in {}.{}".format(byc[ "config" ][ "info_db" ], byc[ "config" ][ "beacon_info_coll"]) )

    b_info = { "date": date_isoformat(datetime.datetime.now()), "datasets": { } }
    for ds in byc["datasets_info"]:
        b_info["datasets"].update( { ds["id"]: _dataset_update_counts(b_info, ds, **byc) } )      

    mongo_client = MongoClient( )
    info_db = mongo_client[ byc[ "config" ][ "info_db" ] ]
    info_coll = info_db[ byc[ "config" ][ "beacon_info_coll"] ]
    info_coll.update_one( { "date" : b_info[ "date" ] }, { "$set": b_info }, upsert=True )
    
    print("=> updated entry in {}.{}".format(byc[ "config" ][ "info_db" ], byc[ "config" ][ "beacon_info_coll"]) )

################################################################################
################################################################################
################################################################################

def _dataset_update_counts(b_info, ds, **byc):

    mongo_client = MongoClient( )

    ds_id = ds["id"]
    ds_db = mongo_client[ ds_id ]
    b_info.update( { ds_id: { "counts": { } } } )
    c_n = ds_db.list_collection_names()
    for c in byc["config"]["collections"]:
        if c in c_n:
            no = ds_db[ c ].estimated_document_count()
            b_info[ ds_id ]["counts"].update( { c: no } )
            if c == "variants":
                v_d = { }
                bar = Bar(ds_id+' variants', max = no, suffix='%(percent)d%%'+" of "+str(no) )
                for v in ds_db[ c ].find({}):
                    v_d[ v["digest"] ] = 1
                    bar.next()
                bar.finish()
                b_info[ ds_id ]["counts"].update( { "variants_distinct": len(v_d.keys()) } )
                b_info[ ds_id ].update( { "filtering_terms": _dataset_get_filters(ds_id, **byc) } )

    return(b_info)

################################################################################
################################################################################
################################################################################

def _dataset_get_filters(ds_id, **byc):

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ ds_id ]
    bios_coll = mongo_db[ 'biosamples' ]

    filter_v = [ ]

    scopes = ( "external_references", "biocharacteristics")

    split_v = re.compile(r'^(\w+?)[\:\-](\w[\w\.]+?)$')

    for s in scopes:

        s_key = s+".type.id"
        afs = bios_coll.distinct( s_key )
        pfs = [ ]
        for k in afs:
            try:
                if split_v.match(k):
                    pre, code = split_v.match(k).group(1, 2)
                    if pre in byc["filter_defs"]:
                        pfs.append( k )
            except:
                continue
        no = len(pfs)
        bar = Bar(ds_id+': '+s, max = no, suffix='%(percent)d%%'+" of "+str(no) )
        for b in pfs:
            bar.next()
            pre, code = split_v.match(b).group(1, 2)          
            l = ""
            labs = bios_coll.find_one( { s_key: b } )
            # the scope list will contain many items, not only for the
            # current code
            for bio_c in labs[ s ]:
                if bio_c[ "type" ][ "id" ] == b:
                    try:
                        l = bio_c[ "type" ][ "label" ]
                        break
                    except:
                        break
            f = {
                "source": byc[ "filter_defs" ][ pre ][ "name" ],
                "id": b,
                "label": l,
                "count": bios_coll.count_documents( { s_key: b } )
            }
            filter_v.append( f )

        bar.finish()

        print("=> {} valid filtering terms out of {} for {}".format(no, len(afs), ds_id) )

    print("=> {} filtering terms for {}".format(len(filter_v), ds_id) )
 
    return(filter_v)

if __name__ == '__main__':
    main()
