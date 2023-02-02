import re, yaml, json
from pymongo import MongoClient
from os import path, pardir, scandir
from pathlib import Path
from json_ref_dict import RefDict, materialize
from humps import camelize, decamelize

################################################################################

def read_bycon_definition_files(byc):

    if not "bycon_definition_files" in byc["config"]:

        config_d = path.join( byc["pkg_path"], "config" )

        b_d_fs = [ f.name for f in scandir(config_d) if f.is_file() ]
        b_d_fs = [ f for f in b_d_fs if f.endswith("yaml") ]
        b_d_fs = [ Path(f).stem for f in b_d_fs if not f.startswith("config.yaml") ]

        byc["config"].update({"bycon_definition_files": b_d_fs})

    for d in byc["config"]["bycon_definition_files"]:
        read_bycon_configs_by_name( d, byc )

    return byc

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
    ofp = path.join( byc["pkg_path"], "config", name+".yaml" )

    with open( ofp ) as od:
        o = yaml.load( od , Loader=yaml.FullLoader)

    byc.update({ name: o })

    return byc

################################################################################

def read_local_prefs(service, dir_path, byc):

    # We use snake_case in the paths
    service = decamelize(service)

    d = Path( path.join( dir_path, "config", service ) )

    # old style named config
    f = Path( path.join( dir_path, "config", service+".yaml" ) )

    if f.is_file():
        byc.update({"service_config": load_yaml_empty_fallback( f ) })
        return byc

    elif d.is_dir():
        t_f_p = Path( path.join( d, "config.yaml" ) )
        if t_f_p.is_file():
            byc.update({ "service_config": load_yaml_empty_fallback(t_f_p) } )

    return byc   

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

def datasets_update_latest_stats(byc, collection_type="datasets"):

    results = [ ]

    def_k = re.sub(r's$', "_definitions", collection_type)
    q_k = re.sub(r's$', "_ids", collection_type)

    stat = dbstats_return_latest(byc)[0]

    for coll_id, coll in byc[ def_k ].items():
        if q_k in byc:
            if len(byc[ q_k ]) > 0:
                if not coll_id in byc[ q_k ]:
                    continue

        if collection_type in stat:
            if coll_id in stat[ collection_type ].keys():
                ds_vs = stat[ collection_type ][coll_id]
                if "counts" in ds_vs:
                    for c, c_d in byc["config"]["beacon_counts"].items():
                        if c_d["info_key"] in ds_vs["counts"]:
                            coll["info"].update({ c: ds_vs["counts"][ c_d["info_key"] ] })
                if "filtering_terms" in byc["response_entity_id"]:
                    coll.update({ "filtering_terms": stat[ collection_type ][coll_id]["filtering_terms"] } )

        results.append(coll)

    return results

################################################################################

def load_yaml_empty_fallback(yp):

    y = { }

    try:
        with open( yp ) as yd:
            y = yaml.load( yd , Loader=yaml.FullLoader)
    except:
        pass

    return y
