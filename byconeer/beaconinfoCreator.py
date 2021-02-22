#!/usr/local/bin/python3

import re, json, yaml
from os import path, environ, pardir
import sys, datetime
from isodate import date_isoformat
from pymongo import MongoClient
from progress.bar import Bar

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.read_specs import read_bycon_configs_by_name
from byconeer.lib import *

"""

## `beaconinfoCreator`

This script reads the Beacon definitions from the configuration files, populates
the filter definition and dataset statistics and saves the information ino the
`progenetix.beaconinfo` database, from where it can be used e.g. by the Beacon
API (`byconplus`).

"""

################################################################################
################################################################################
################################################################################

def main():

    byc = initialize_service("collations")

    b_info = { "date": date_isoformat(datetime.datetime.now()), "datasets": { } }

    print("=> updating entry {} in {}.{}".format(b_info[ "date" ], byc[ "config" ][ "info_db" ], byc[ "config" ][ "beacon_info_coll"]) )

    mongo_client = MongoClient( )
    dbs = MongoClient().list_database_names()

    for ds_id in byc["dataset_definitions"].keys():
        if not ds_id in dbs:
            print("¡¡¡ Dataset "+ds_id+" doesn't exist !!!")
        else:
            b_info["datasets"].update( { ds_id: _dataset_update_counts(byc["dataset_definitions"][ds_id], **byc) } )      
    info_db = mongo_client[ byc[ "config" ][ "info_db" ] ]
    info_coll = info_db[ byc[ "config" ][ "beacon_info_coll"] ]
    info_coll.delete_many( { "date": b_info["date"] } ) #, upsert=True
    info_coll.insert_one( b_info ) #, upsert=True 
    
    print("=> updated entry {} in {}.{}".format(b_info["date"], byc[ "config" ][ "info_db" ], byc[ "config" ][ "beacon_info_coll"]) )

################################################################################
################################################################################
################################################################################

def _dataset_update_counts(ds, **byc):

    mongo_client = MongoClient( )

    ds_id = ds["id"]
    ds_db = mongo_client[ ds_id ]
    b_i_ds = { "counts": { }, "filtering_terms": [ ] }
    c_n = ds_db.list_collection_names()
    for c in byc["config"]["collections"]:
        if c in c_n:
            no = ds_db[ c ].estimated_document_count()
            b_i_ds["counts"].update( { c: no } )
            if c == "variants":
                v_d = { }
                bar = Bar(ds_id+' variants', max = no, suffix='%(percent)d%%'+" of "+str(no) )
                for v in ds_db[ c ].find({}):
                    if "digest" in v:
                        v_d[ v["digest"] ] = 1
                    bar.next()
                bar.finish()
                b_i_ds["counts"].update( { "variants_distinct": len(v_d.keys()) } )
    
    if b_i_ds["counts"]["biosamples"] > 0:
        b_i_ds.update( { "filtering_terms": _dataset_count_collationed_filters(ds_id, **byc) } )

    return(b_i_ds)

################################################################################

def _dataset_count_collationed_filters(ds_id, **byc):

    mongo_client = MongoClient( )
    mongo_db = mongo_client[ ds_id ]
    bios_coll = mongo_db[ 'biosamples' ]

    sample_no =  bios_coll.estimated_document_count()

    filter_v = [ ]

    scopes = ( "external_references", "biocharacteristics", "cohorts" )

    split_v = re.compile(r'^(\w+?)[\:\-].+?$')

    for s in scopes:
        pfs = { }
        source_key = s+".id"
        afs = bios_coll.distinct( source_key )
        for k in afs:
            try:
                if split_v.match(k):
                    pre = split_v.match(k).group(1)

                    if pre in byc["these_prefs"]["collationed"]:
                        coll_p = re.compile( byc["these_prefs"]["collationed"][ pre ]["pattern"] )
                        if coll_p.match(k):
                            pfs.update( { k: { 
                                "id": k,
                                "count": 0,
                                # "source": byc[ "filter_definitions" ][ pre ][ "name" ],
                                # "scope": s
                            } } )
            except:
                continue
        scopedNo = len(pfs.keys())
        if scopedNo > 0:
            bar = Bar(ds_id+': '+s, max = sample_no, suffix='%(percent)d%%'+" of "+str(sample_no) )
            for sample in bios_coll.find({}):
                bar.next()
                if s in sample:
                    for term in sample[ s ]:
                        tid = term["id"]
                        if tid in pfs.keys():
                            pfs[ tid ]["count"] += 1
                            if "label" in term:
                                 pfs[ tid ]["label"] = term["label"]

            bar.finish()

            print("=> {} valid filtering terms out of {} for {} ({})".format(scopedNo, len(afs), s, ds_id) )

            for fk, ft in pfs.items():
                # print("{}: {}".format(ft["id"], ft["count"]))
                filter_v.append(ft)

    print("=> {} filtering terms for {}".format(len(filter_v), ds_id) )
 
    return filter_v

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
