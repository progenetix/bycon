import re, yaml
import json
from pymongo import MongoClient
from os import path, pardir
from json_ref_dict import RefDict, materialize

from cgi_utils import *

################################################################################

def read_bycon_configs_by_name(name, byc):

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

    byc.update({ name: o })

    # TODO Move ...

    if name == "beacon":
        byc.update({ "beacon-schema": RefDict(ofp) })

    return byc

################################################################################

def read_local_prefs(service, dir_path):

    p = path.join( dir_path, "config", service+".yaml" )

    return load_yaml( p )

################################################################################

def read_yaml_with_key_to_object(file_key, data_key, **paths):

    o = load_yaml( path.join( paths[ "module_root" ], *paths[ file_key ] ) )

    if data_key in o:
        return o[ data_key ]

    # TODO: error capture & procedure

    return o

################################################################################

def dbstats_return_latest(byc):

    limit = 1
    if "stats_number" in byc:
        if byc["stats_number"] > 1:
            limit = byc["stats_number"]

    db = byc[ "config" ][ "info_db" ]
    coll = byc[ "config" ][ "beacon_info_coll" ]

    stats = MongoClient( )[ db ][ coll ].find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( limit )
    return stats

################################################################################

def datasets_update_latest_stats(byc):

    datasets = [ ]

    stat = dbstats_return_latest(byc)[0]

    for ds_id, ds in byc["dataset_definitions"].items():
        if "dataset_ids" in byc:
            if len(byc[ "dataset_ids" ]) > 0:
                if not ds_id in byc[ "dataset_ids" ]:
                    continue
        if ds_id in stat["datasets"].keys():
            ds_vs = stat["datasets"][ds_id]
            if "counts" in ds_vs:
                for c, c_d in byc["config"]["beacon_counts"].items():
                    if c_d["info_key"] in ds_vs["counts"]:
                        ds.update({ c: ds_vs["counts"][ c_d["info_key"] ] })

        datasets.append( ds )

    return datasets

################################################################################

def update_datasets_from_dbstats(byc):

    ds_with_counts = datasets_update_latest_stats(byc)

    if not "beacon_info" in byc:
        byc["beacon_info"] = { }
    byc["beacon_info"].update( { "datasets": ds_with_counts } )

    if "service_info" in byc:
        for par in byc[ "beacon_info" ]:
            byc[ "service_info" ].update( { par: byc[ "beacon_info" ][ par ] } )

    return byc

################################################################################

def load_yaml(yp):

    y = { }

    try:
        with open( yp ) as yd:
            y = yaml.load( yd , Loader=yaml.FullLoader)
    except:
        pass

    return y

