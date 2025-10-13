# __init__.py
import sys, traceback
from os import path

pkg_path = path.dirname( path.abspath(__file__) )
sys.path.append( pkg_path )

from config import *

bycon_lib_path = path.join( pkg_path, "lib" )
sys.path.append( bycon_lib_path )

# try block to give at least some feedback on errors
try:

    from beacon_auth import *
    from beacon_response_generation import *
    from bycon_helpers import *
    from bycon_info import *
    from bycon_summarizer import *
    from genome_utils import *
    from handover_generation import *
    from interval_utils import *
    from parameter_parsing import *
    from query_execution import *
    from query_generation import *
    from response_remapping import *
    from schema_parsing import *
    from variant_mapping import *
    from vrs_translator import *

    # base configuration #######################################################

    """
    Reading the config from the same wrapper dir:
    module
      |
      |- lib - read_specs.py
      |- definitions - __name__.yaml
    """
    if not path.isdir(CONF_PATH):
        sys.exit(f"Config directory {CONF_PATH} does not exist.")
    b_d_fs = [ f.name for f in scandir(CONF_PATH) if f.is_file() ]
    b_d_fs = [ f for f in b_d_fs if f.endswith("yaml") ]
    for d in [ Path(f).stem for f in b_d_fs ]:
        o = load_yaml_empty_fallback(path.join(CONF_PATH, f'{d}.yaml' ))
        BYC.update({d: o})

    e_d = always_merger.merge(
        BYC.get("entity_defaults", {}),
        BYC.get("services_entity_defaults", {})
    )

    BYC.update({"entity_defaults": e_d})

    # local configuration ######################################################

    """Overwriting of installation-wide defaults with instance-specific ones
    _i.e._ matching the current domain (to allow presentation of different
    Beacon instances from the same server)"""

    dom_df_p = path.join(LOC_PATH, "domain_definitions")
    if path.isdir(dom_df_p):
        doms = [ f.name for f in scandir(dom_df_p) if f.is_file() ]
        doms = [ Path(f).stem for f in doms if f.endswith("yaml") ]

        # first general info & defaults
        if "localhost" in doms:
            doms = doms.pop(doms.index("localhost"))
            ld = load_yaml_empty_fallback(path.join(dom_df_p, "localhost.yaml" ))
            BYC.update({
                "beacon_defaults": always_merger.merge(BYC.get("beacon_defaults", {}), ld.get("beacon_defaults", {})),
                "entity_defaults": always_merger.merge(BYC.get("entity_defaults", {}), ld.get("entity_defaults", {}))
            })

        # server specific setting of defaults dataset ids etc.
        if not "___shell___" in ENV:
            instance = None
            for dr in doms:
                dd = load_yaml_empty_fallback(path.join(dom_df_p, f"{dr}.yaml" ))
                ddoms = dd.get("domains", [])
                if environ.get("HTTP_HOST", "___none___") in ddoms:
                    BYC.update({
                        "beacon_defaults": always_merger.merge(BYC.get("beacon_defaults", {}), dd.get("beacon_defaults", {})),
                        "entity_defaults": always_merger.merge(BYC.get("entity_defaults", {}), dd.get("entity_defaults", {}))
                    })

    # TODO: better way to define which files are parsed from local
    for p in BYC.get("loc_mod_pars", []):
        f = path.join(LOC_PATH, f'{p}.yaml')
        d = load_yaml_empty_fallback(f)
        prdbug(f'...LOC_PATH file => {p}')
        BYC.update({p: always_merger.merge(BYC.get(p, {}), d)})

    ds_df_p = path.join(LOC_PATH, "dataset_definitions")
    if path.isdir(ds_df_p):
        ds_df_f = [ f.name for f in scandir(ds_df_p) if f.is_file() ]
        ds_df_f = [ f for f in ds_df_f if f.endswith("yaml") ]
        for d in [ Path(f).stem for f in ds_df_f ]:
            df = load_yaml_empty_fallback(path.join(ds_df_p, f'{d}.yaml' ))
            BYC["dataset_definitions"].update({d: always_merger.merge(BYC["dataset_definitions"].get(d, {}), df)})

    if (defaults := BYC["beacon_defaults"].get("defaults", {})):
        for d_k, d_v in defaults.items():
            BYC.update( { d_k: d_v } )

    # / configuration ##########################################################

    # parameters and resulting modifications ###################################

    ByconParameters().set_parameters()
    ByconEntities().set_entities()
    ByconDatasets().set_dataset_ids()

    BYC.update({"TEST_MODE": ByconH().truth(BYC_PARS.get("test_mode"))})

    set_user_name()
    set_returned_granularities()    

    # / parameters & modifications #############################################

except Exception:
    if not "___shell___" in ENV:
        print('Content-Type: text/plain')
        print('status: 302')
        print()
    
    print(traceback.format_exc())
    print()
    exit()


