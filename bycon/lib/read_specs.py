import inspect, json, re, yaml
from deepmerge import always_merger
from humps import camelize, decamelize
from json_ref_dict import RefDict, materialize
from os import path, pardir, scandir, environ
from pathlib import Path
from pymongo import MongoClient

from cgi_parsing import prdbug

################################################################################

def read_service_definition_files(byc):

    pkg_path = byc.get("pkg_path", "___none___")
    conf_dir = path.join( pkg_path, "config")

    b_d_fs =[]

    if not path.isdir(conf_dir):
        return

    if len(b_d_fs) < 1:

        b_d_fs = [ f.name for f in scandir(conf_dir) if f.is_file() ]
        b_d_fs = [ f for f in b_d_fs if f.endswith("yaml") ]
        b_d_fs = [ Path(f).stem for f in b_d_fs ]

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

    o = {}
    ofp = path.join( conf_dir, f'{name}.yaml' )

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

def update_rootpars_from_local(loc_dir, byc):

    # avoiding re-parsing of directories, e.g. during init stage
    p_c_p = byc.get("parsed_config_paths", [])
    if loc_dir in p_c_p:
        return

    p_c_p.append(loc_dir)

    b_p = 'beacon_defaults'
    s_p = 'services_defaults'

    b_f = path.join(loc_dir, f'{b_p}.yaml')
    b = load_yaml_empty_fallback(b_f)
    s_f = path.join(loc_dir, f'{s_p}.yaml')
    s = load_yaml_empty_fallback(s_f)
    b = always_merger.merge(s, b)
    byc.update({b_p: always_merger.merge(byc.get(b_p, {}), b)})

    # TODO: better way to define which files are parsed from local
    for p in ("authorizations", "dataset_definitions", "local_paths", "local_parameters", "datatable_mappings", "plot_defaults"):
        f = path.join(loc_dir, f'{p}.yaml')
        d = load_yaml_empty_fallback(f)
        byc.update({p: always_merger.merge(byc.get(p, {}), d)})

    return


################################################################################

def dbstats_return_latest(byc):

    # TODO: This is too hacky & should be moved to an external function
    # which updates the database_definitions / beacon_info yamls...
    info_db = byc["housekeeping_db"]
    coll = byc["beacon_info_coll"]
    stats = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))[ info_db ][ coll ].find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( 1 )
    return list(stats)[0]


################################################################################

def datasets_update_latest_stats(byc, collection_type="datasets"):

    results = [ ]

    def_k = re.sub(r's$', "_definitions", collection_type)
    q_k = re.sub(r's$', "_ids", collection_type)

    stat = dbstats_return_latest(byc)

    for coll_id, coll in byc[ def_k ].items():
        if q_k in byc:
            if len(byc[ q_k ]) > 0:
                if not coll_id in byc[ q_k ]:
                    continue

        if collection_type in stat:
            if coll_id in stat[ collection_type ].keys():
                ds_vs = stat[ collection_type ][coll_id]
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
        pass
    return y

