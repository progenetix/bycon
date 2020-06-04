#!/usr/local/bin/python3

import re, json, yaml
from os import path as path
from os import environ
import sys, os, datetime, logging, argparse
from isodate import date_isoformat
from pymongo import MongoClient
from progress.bar import IncrementalBar
# from progress.bar import Bar

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""

This script reads the Becon definitions from the configuration file, populates
the filter definition and dataset statistics and saves the enriched beacon info
as YAML file, to be read in by the `byconplus` web service.

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
    byc.update( { "dbstats": dbstats_return_latest( **byc ) } )
    byc.update( { "beacon_info": read_beacon_info( **byc ) } )    
    byc.update( { "service_info": read_service_info( **byc ) } )
    byc.update( { "datasets_info": read_datasets_info( **byc ) } )

    for par in byc[ "beacon_info" ]:
        byc[ "service_info" ][ par ] = byc[ "beacon_info" ][ par ]

    ds_with_counts = [ ]

    print("=> updating entry in {}.{}".format(byc[ "config" ][ "info_db" ], byc[ "config" ][ "beacon_info_coll"]) )

    b_info = { "date": date_isoformat(datetime.datetime.now()) }
    for ds in byc["datasets_info"]:
        b_info = _dataset_update_counts(b_info, ds, **byc)      

    info_db = mongo_client[ byc[ "config" ][ "info_db" ] ]
    info_coll = info_db[ byc[ "config" ][ "beacon_info_coll"] ]
    info_coll.update_one( { "date" : b_info[ "date" ] }, { "$set": b_info }, upsert=True )
    
    mongo_client = MongoClient( )
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
            b_info[ ds_id ]["counts"].update( { c: ds_db[ c ].estimated_document_count() } )
            if c == "variants":
                v_d = { }
                bar = IncrementalBar(ds_id+' variants', max = ds_db[ c ].estimated_document_count() )
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
        pfs = [ ]
        for k in bios_coll.distinct( s_key ):
            if split_v.match(k):
                pre, code = split_v.match(k).group(1, 2)
                if pre in byc["filter_defs"]:
                    pfs.append( k )

        bar = IncrementalBar(ds_id+': '+s, max = len(pfs) )
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

        print("=> {} valid filtering terms out of {} for {}".format(len(filter_v), len(pfs), ds_id) )

    return(filter_v)

if __name__ == '__main__':
    main()
