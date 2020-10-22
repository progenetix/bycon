import re, yaml
import json
from pymongo import MongoClient
from os import path as path
from os import environ

from .cgi_utils import *

################################################################################

def read_named_prefs(service, dir_path):

    o = {}
    ofp = path.join( dir_path, "..", "bycon", "config", service+".yaml" )
    with open( ofp ) as od:
        o = yaml.load( od , Loader=yaml.FullLoader)    
    return o

################################################################################

def read_local_prefs(service, dir_path):

    o = {}
    ofp = path.join( dir_path, "config", service+".yaml" )
    with open( ofp ) as od:
        o = yaml.load( od , Loader=yaml.FullLoader)    
    return o

################################################################################

def read_yaml_with_key_to_object(file_key, data_key, **paths):

    o = {}
    ofp = path.join( paths[ "module_root" ], *paths[ file_key ] )
    with open( ofp ) as od:
        o = yaml.load( od , Loader=yaml.FullLoader)

    if data_key in o:
        return o[ data_key ]

    # TODO: error capture & procedure

    return o

################################################################################

def dbstats_return_latest( **byc ):

    db = byc[ "config" ][ "info_db" ]
    coll = byc[ "config" ][ "beacon_info_coll" ]

    stats = MongoClient( )[ db ][ coll ].find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( 1 )
    return(stats[0])

################################################################################

def update_datasets_from_dbstats(**byc):

    ds_with_counts = [ ]
    for ds_id in byc["dataset_definitions"].keys():
        ds = byc["dataset_definitions"][ds_id]
        if ds_id in byc["dbstats"]["datasets"]:
            ds_db = byc["dbstats"]["datasets"][ ds_id ]
            for k, l in byc["config"]["beacon_info_count_labels"].items():
                if "counts" in ds_db:
                    if k in ds_db["counts"]:
                        ds[ l ] = ds_db["counts"][ k ]
        ds_with_counts.append(ds)

    return(ds_with_counts)
