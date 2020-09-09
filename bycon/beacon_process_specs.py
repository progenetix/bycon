import re, yaml
import json
from pymongo import MongoClient
from os import path as path
from os import environ

from .cgi_utils import *

################################################################################

def read_bycon_config( module_path ):
    
    with open( path.join( module_path, '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( module_path, '..' )
    config[ "paths" ][ "out" ] = path.join( *config[ "paths" ][ "web_temp_dir_abs" ] )

    return config

################################################################################

def read_named_prefs(service, dir_path):

    o = {}
    ofp = path.join( dir_path, "..", "config", service+".yaml" )
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

def read_filter_definitions( **paths ):

    filter_defs = {}
    ofp = path.join( paths[ "module_root" ], *paths[ "filter_definitions_file" ] )
    with open( ofp ) as fd:
        defs = yaml.load( fd , Loader=yaml.FullLoader)
        for fpre in defs:
            filter_defs[fpre] = defs[fpre]
    
    return filter_defs

################################################################################

def dbstats_return_latest( **config ):

    dbstats_coll = MongoClient( )[ config[ "info_db" ] ][ config[ "beacon_info_coll" ] ]
    stats = dbstats_coll.find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( 1 )
    return(stats[0])

################################################################################

def update_datasets_from_dbstats(**byc):

    ds_with_counts = [ ]
    for ds_id in byc["datasets_info"].keys():
        ds = byc["datasets_info"][ds_id]
        if ds_id in byc["dbstats"]["datasets"]:
            ds_db = byc["dbstats"]["datasets"][ ds_id ]
            for k, l in byc["config"]["beacon_info_count_labels"].items():
                if "counts" in ds_db:
                    if k in ds_db["counts"]:
                        ds[ l ] = ds_db["counts"][ k ]
        ds_with_counts.append(ds)

    return(ds_with_counts)
