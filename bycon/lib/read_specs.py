import json, yaml
from deepmerge import always_merger
from json_ref_dict import RefDict, materialize
from os import path, pardir, scandir, environ
from pathlib import Path

from config import *
from bycon_helpers import load_yaml_empty_fallback, prdbug, prdbughead

################################################################################

def read_service_definition_files():
    """
    Reading the config from the same wrapper dir:
    module
      |
      |- lib - read_specs.py
      |- definitions - __name__.yaml
    """
    if not path.isdir(CONF_PATH):
        return
    b_d_fs = [ f.name for f in scandir(CONF_PATH) if f.is_file() ]
    b_d_fs = [ f for f in b_d_fs if f.endswith("yaml") ]
    b_d_fs = [ Path(f).stem for f in b_d_fs ]

    for d in b_d_fs:
        o = load_yaml_empty_fallback(path.join(CONF_PATH, f'{d}.yaml' ))
        BYC.update({d: o})        

    e_d = always_merger.merge(
        BYC.get("entity_defaults", {}),
        BYC.get("services_entity_defaults", {})
    )

    BYC.update({"entity_defaults": e_d})


################################################################################

def update_rootpars_from_local_or_HOST():
    """Overwriting of installation-wide defaults with instance-specific ones
    _i.e._ matching the current domain (to allow presentation of different
    Beacon instances from the same server)"""

    i_ovr = load_yaml_empty_fallback(path.join(LOC_PATH, "instance_definitions.yaml"))

    if "local" in i_ovr:
        i_o_bdfs = i_ovr["local"].get("beacon_defaults", {})
        i_o_edfs = i_ovr["local"].get("entity_defaults", {})
        BYC.update({"beacon_defaults": always_merger.merge(BYC.get("beacon_defaults", {}), i_o_bdfs)})
        BYC.update({"entity_defaults": always_merger.merge(BYC.get("entity_defaults", {}), i_o_edfs)})
    if not "___shell___" in ENV:
        instance = "___none___"
        host = environ.get("HTTP_HOST", "___none___")
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
    for p in BYC.get("loc_mod_pars", []):
        f = path.join(LOC_PATH, f'{p}.yaml')
        d = load_yaml_empty_fallback(f)
        prdbug(f'...LOC_PATH file => {p}')
        BYC.update({p: always_merger.merge(BYC.get(p, {}), d)})

    return

