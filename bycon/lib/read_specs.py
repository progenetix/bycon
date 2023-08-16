import re, yaml, json
from pymongo import MongoClient
from os import path, pardir, scandir, environ
from pathlib import Path
from json_ref_dict import RefDict, materialize
from humps import camelize, decamelize

################################################################################

def read_bycon_definition_files(conf_dir, byc):

    b_d_fs =[]

    if not path.isdir(conf_dir):
        return

    if len(b_d_fs) < 1:

        b_d_fs = [ f.name for f in scandir(conf_dir) if f.is_file() ]
        b_d_fs = [ f for f in b_d_fs if f.endswith("yaml") ]
        b_d_fs = [ Path(f).stem for f in b_d_fs if not f.startswith("config.yaml") ]

    for d in b_d_fs:
        read_bycon_configs_by_name( d, conf_dir, byc )

################################################################################
  
def read_bycon_configs_by_name(name, conf_dir, byc):

    """podmd
    Reading the config from the same wrapper dir:
    module
      |
      |- lib - read_specs.py
      |- config - __name__.yaml
    podmd"""

    # print(name)

    o = {}
    ofp = path.join( conf_dir, name+".yaml" )

    with open( ofp ) as od:
        o = yaml.load( od , Loader=yaml.FullLoader)

    byc.update({ name: o })

################################################################################

def read_service_prefs(service, service_pref_path, byc):

    # snake_case paths; e.g. `intervalFrequencies` => `interval_frequencies.yaml`
    service = decamelize(service)

    f = Path( path.join( service_pref_path, service+".yaml" ) )
    if f.is_file():
        byc.update({"service_config": load_yaml_empty_fallback( f ) })

################################################################################

def dbstats_return_latest(byc):

    # TODO: This is too hacky & should be moved to an external function
    # which updates the database_definitions / beacon_info yamls...

    limit = 1
    # if "stats_number" in byc:
    #     if byc["stats_number"] > 1:
    #         limit = byc["stats_number"]

    info_db = byc[ "config" ][ "housekeeping_db" ]
    coll = byc[ "config" ][ "beacon_info_coll" ]
    stats = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))[ info_db ][ coll ].find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( limit )
    return list(stats)

################################################################################

def datasets_update_latest_stats(byc, collection_type="datasets"):

    results = [ ]

    def_k = re.sub(r's$', "_definitions", collection_type)
    q_k = re.sub(r's$', "_ids", collection_type)

    stat = dbstats_return_latest(byc)[0]

    counted = byc["config"].get("beacon_count_items", {})

    for coll_id, coll in byc[ def_k ].items():
        if q_k in byc:
            if len(byc[ q_k ]) > 0:
                if not coll_id in byc[ q_k ]:
                    continue

        if collection_type in stat:
            if coll_id in stat[ collection_type ].keys():
                ds_vs = stat[ collection_type ][coll_id]
                if "counts" in ds_vs:
                    for c, c_d in counted.items():
                        i_k = c_d.get("info_key", "___none___")
                        if i_k in ds_vs["counts"]:
                            coll["info"].update({ c: ds_vs["counts"][ i_k ] })
                if "filtering_terms" in byc["response_entity_id"]:
                    coll.update({ "filtering_terms": stat[ collection_type ][coll_id].get("filtering_terms", []) } )

        results.append(coll)

    return results

################################################################################

def load_yaml_empty_fallback(yp):

    y = { }

    try:
        with open( yp ) as yd:
            y = yaml.load( yd , Loader=yaml.FullLoader)
    except:
        return y

    return y
