import re, yaml
import json
from pymongo import MongoClient
from os import path, pardir

from .cgi_utils import *

################################################################################

def read_bycon_configs_by_name(name):

    """podmd
    Reading the config from the same wrapper dir:
    module
      |
      |- lib - read_specs.py
      |- config - __name__.yaml
    podmd"""

    o = {}
    ofp = path.join( path.dirname( path.abspath(__file__) ), pardir, "config", name+".yaml" )
    with open( ofp ) as od:
        o = yaml.load( od , Loader=yaml.FullLoader)    
    return o

################################################################################

def read_local_prefs(service, dir_path):

    return load_yaml( path.join( dir_path, "config", service+".yaml" ) )

################################################################################

def read_yaml_with_key_to_object(file_key, data_key, **paths):

    o = load_yaml( path.join( paths[ "module_root" ], *paths[ file_key ] ) )

    if data_key in o:
        return o[ data_key ]

    # TODO: error capture & procedure

    return o

################################################################################

def dbstats_return_latest( limit, **byc ):

    if not limit:
        limit = 1

    db = byc[ "config" ][ "info_db" ]
    coll = byc[ "config" ][ "beacon_info_coll" ]

    stats = MongoClient( )[ db ][ coll ].find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( limit )
    return stats

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

################################################################################

def load_yaml(yp):

    y = { }

    try:
        with open( yp ) as yd:
            y = yaml.load( yd , Loader=yaml.FullLoader)
    except:
        pass

    return y

