import inspect, json, re, yaml
from deepmerge import always_merger
from json_ref_dict import RefDict, materialize
from os import path, pardir, scandir, environ
from pathlib import Path
from pymongo import MongoClient

from cgi_parsing import prdbug
from cytoband_parsing import parse_cytoband_file
from config import *

################################################################################

def read_service_definition_files(byc):
    """podmd
    Reading the config from the same wrapper dir:
    module
      |
      |- lib - read_specs.py
      |- definitions - __name__.yaml
    podmd"""
    conf_dir = path.join(PKG_PATH, "definitions")
    if not path.isdir(conf_dir):
        return
    b_d_fs = [ f.name for f in scandir(conf_dir) if f.is_file() ]
    b_d_fs = [ f for f in b_d_fs if f.endswith("yaml") ]
    b_d_fs = [ Path(f).stem for f in b_d_fs ]

    for d in b_d_fs:
        o = {}
        ofp = path.join( conf_dir, f'{d}.yaml' )
        with open( ofp ) as od:
            o = yaml.load( od , Loader=yaml.FullLoader)
        if d in BYC.keys():
            BYC.update({d: o})
        else:
            byc.update({d: o})

    parse_cytoband_file(byc)

################################################################################

def set_entity_mappings():
    b_e_d = BYC.get("entity_defaults", {})
    p_e_m = BYC.get("path_entry_type_mappings", {})
    e_p_m = BYC.get("entry_type_path_mappings", {})
    d_p_e = BYC.get("data_pipeline_entities", [])
    for e, e_d in b_e_d.items():
        if (p := e_d.get("request_entity_path_id")):
            p_e_m.update({ p: e })
            e_p_m.update({ e: p })
        for a in e_d.get("request_entity_path_aliases", []):
            p_e_m.update({ a: e })
        if "beaconResultsetsResponse" in e_d.get("response_schema", ""):
            d_p_e.append(e)


################################################################################

def update_rootpars_from_local(loc_dir, byc):
    # avoiding re-parsing of directories, e.g. during init stage
    p_c_p = byc.get("parsed_config_paths", [])
    if loc_dir in p_c_p:
        return

    p_c_p.append(loc_dir)
    s_f = path.join(loc_dir, 'services_entity_defaults.yaml')
    s = load_yaml_empty_fallback(s_f)
    BYC.update({"entity_defaults": always_merger.merge(BYC.get("entity_defaults", {}), s)})

    # overwriting installation-wide defaults with instance-specific ones
    # _i.e._ matching the current domain (to allow presentation of different
    # Beacon instances from the same server)
    i_ovr_f = path.join(loc_dir, "instance_overrides.yaml")
    i_ovr = load_yaml_empty_fallback(i_ovr_f)

    if "local" in i_ovr:
        i_o_bdfs = i_ovr["local"].get("beacon_defaults", {})
        i_o_edfs = i_ovr["local"].get("entity_defaults", {})
        BYC.update({"beacon_defaults": always_merger.merge(BYC.get("beacon_defaults", {}), i_o_bdfs)})
        BYC.update({"entity_defaults": always_merger.merge(BYC.get("entity_defaults", {}), i_o_edfs)})
    if not "local" in ENV:
        instance = "___none___"
        host = environ.get("HTTP_HOST", "local")
        for i_k, i_v in i_ovr.items():
            doms = i_v.get("domains", [])
            if host in doms:
                instance = i_k
                break
        if instance in i_ovr:
            i_o_bdfs = i_ovr[instance].get("beacon_defaults", {})
            i_o_edfs = i_ovr[instance].get("entity_defaults", {})
            BYC.update({"beacon_defaults": always_merger.merge(BYC.get("beacon_defaults", {}), i_o_bdfs)})
            BYC.update({"entity_defaults": always_merger.merge(BYC.get("entity_defaults", {}), i_o_edfs)})

    # TODO: better way to define which files are parsed from local
    for p in ("authorizations", "dataset_definitions", "local_paths", "local_parameters", "datatable_mappings", "plot_defaults"):
        f = path.join(loc_dir, f'{p}.yaml')
        d = load_yaml_empty_fallback(f)
        prdbug(f'...loc_dir file => {p}')
        if p in BYC.keys():
            BYC.update({p: always_merger.merge(BYC.get(p, {}), d)})
        else:
            byc.update({p: always_merger.merge(byc.get(p, {}), d)})

    return


################################################################################

def dbstats_return_latest(byc):
    # TODO: This is too hacky & should be moved to an external function
    # which updates the database_definitions / beacon_info yamls...
    stats = MongoClient(host=DB_MONGOHOST)[HOUSEKEEPING_DB][HOUSEKEEPING_INFO_COLL].find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( 1 )
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
    y = {}
    try:
        # print(yp)
        with open( yp ) as yd:
            y = yaml.load( yd , Loader=yaml.FullLoader)
    except Exception as e:
        # print(e)
        pass
    return y

