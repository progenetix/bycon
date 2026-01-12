# __init__.py

"""
bycon package initialization module.

Handles:
- Path configuration
- Module imports
- Configuration loading
- Parameter processing
"""

import sys, logging, traceback
from deepmerge import always_merger
from os import path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# try block to give at least some feedback on errors
try:
    pkg_path = path.dirname(path.abspath(__file__))
    sys.path.append(pkg_path)
    from config import *

    # the package namespace imports _all_ functions from _all_ modules

    bycon_lib_path = path.join( pkg_path, "lib" )
    sys.path.append( bycon_lib_path )

    from beacon_auth import *
    from beacon_responses import *
    from bycon_helpers import *
    from bycon_summaries import *
    from bycon_info import *
    from genome_utils import *
    from interval_utils import *
    from parameter_parsing import *
    from query_execution import *
    from query_generation import *
    from response_remapping import *
    from schema_parsing import *
    from variant_mapping import *
    from vrs_translator import *

    # Configuration: Loading Stage #############################################

    """
    Reading the config from the same wrapper dir:
    module
      |
      |- config - __name__.yaml
    """

    # Validate config directory exists
    if not path.isdir(CONF_PATH):
        raise FileNotFoundError(f"Config directory {CONF_PATH} does not exist.")

    # Load configurations from package config directory
    b_d_fs = [
        f.name for f in scandir(CONF_PATH) if f.is_file() and f.name.endswith("yaml")
    ]
    for d in [Path(f).stem for f in b_d_fs]:
        try:
            config_file = path.join(CONF_PATH, f'{d}.yaml')
            config_data = load_yaml_empty_fallback(config_file)
            BYC.update({d: config_data})
        except Exception as e:
            logger.error(f"Failed to load {config_file}: {str(e)}")
            raise

    # Load local configurations for predefined modification parameters
    for p in BYC.get("loc_mod_pars", []):
        try:
            local_file = path.join(LOC_PATH, f'{p}.yaml')
            if not path.exists(local_file):
                logger.warning(f"Local config {local_file} not found")
                continue

            local_data = load_yaml_empty_fallback(local_file)
            BYC.update({p: always_merger.merge(BYC.get(p, {}), local_data)})
        except Exception as e:
            logger.error(f"Error processing {p}: {str(e)}")
            raise

    # Load dataset definitions
    ds_df_p = path.join(LOC_PATH, "dataset_definitions")
    if path.isdir(ds_df_p):
        ds_df_f = [
            f.name for f in scandir(ds_df_p)
            if f.is_file() and f.name.endswith("yaml")
        ]
        for d in [Path(f).stem for f in ds_df_f]:
            try:
                df_file = path.join(ds_df_p, f'{d}.yaml')
                dataset_data = load_yaml_empty_fallback(df_file)
                BYC["dataset_definitions"].update({d: always_merger.merge(
                    BYC["dataset_definitions"].get(d, {}),
                    dataset_data
                )})
            except Exception as e:
                logger.error(f"Error loading dataset {d}: {str(e)}")
                raise

    # Configuration: End of Loading Stage ######################################

    # Configuration: Entry types and endpoints #################################

    # Merging Beacon & Services entryTypes but adding a flag to the Beacon ones
    b_e_t       = BYC.get("beacon_configuration",   {}).get("entryTypes", {})
    s_e_t       = BYC.get("services_configuration", {}).get("entryTypes", {})
    e_d         = always_merger.merge(b_e_t, s_e_t)
    for e_k in list(b_e_t.keys()):
        e_d[e_k].update({"is_beacon_entity": True})

    # modifying aliases in definitions with global variables
    for v in ["BEACON_ROOT", "BEACON_API_VERSION"]:
        if (r_v := globals().get(v)):
            e_d = dict_replace_values(e_d, f"___{v}___", r_v)

    # Mapping of entryTypes to endpoints using the default map
    endpoints   = BYC.get("beacon_map",     {}).get("endpointSets", {})
    services    = BYC.get("services_map",   {}).get("endpointSets", {})
    infos       = BYC.get("beacon_map",     {}).get("informationalEndpoints", {})

    for e in list(endpoints.values()) + list(infos.values()) + list(services.values()):
        if not (e_id := e.get("entryType", "___none___")) in e_d:
            continue
        if (e_path_id := e.get("rootUrl")):
            e_path_id = e_path_id.strip("/").split("/")[-1].strip("/")
            if e_path_id == "beacon":
                e_path_id = "info"
            e_d[e_id].update({"request_entity_path_id": e_path_id})
        if (e_path_aliases := e.get("rootUrlAliases")):
            e_a_s = []
            for e_a in e_path_aliases:
                e_a_id = e_a.strip("/").split("/")[-1].strip("/")
                if e_a_id in ["beacon", "services"]:
                    e_a_id = "info"
                e_a_s.append(e_a_id)
            e_d[e_id].update({"request_entity_path_aliases": e_a_s})

    BYC.update({"entity_defaults": e_d})

    # Configuration: End of entry types and endpoints ##########################

    # Configuration: local webserver ###########################################

    """Overwriting of installation-wide defaults with instance-specific ones
    _i.e._ matching the current domain (to allow presentation of different
    Beacon instances from the same server)"""
    
    if path.isdir(dom_df_p := path.join(LOC_PATH, "domain_definitions")):
        doms = [ f.name for f in scandir(dom_df_p) if f.is_file() and f.name.endswith("yaml") ]
        doms = [ Path(f).stem for f in doms ]

        # server specific setting of defaults dataset ids etc.
        if not "___shell___" in HTTP_HOST:
            for dr in doms:
                prdbug(f'...checking domain definition => {dr}')
                dd = load_yaml_empty_fallback(path.join(dom_df_p, f"{dr}.yaml" ))
                ddoms = dd.get("domains", []) + dd.get("test_domains", [])
                if HTTP_HOST in ddoms:
                    if (dds_id := dd.get("default_dataset_id")):
                        BYC.update({"default_dataset_id": dds_id})
                    if (t_doms := dd.get("test_domains")):
                        BYC.update({"test_domains": t_doms})
                    BYC.update({
                        "entity_defaults": always_merger.merge(
                            BYC.get("entity_defaults", {}),
                            dd.get("entity_defaults", {})
                        )
                    })

    # Configuration: End of local webserver ####################################

    # parameters and resulting modifications ###################################

    ByconParameters().set_parameters()
    ByconEntities().set_entities()
    ByconDatasets().set_dataset_ids()

    # Global setting of the TEST_MODE flag for the current request
    BYC.update({"TEST_MODE": ByconH().truth(BYC_PARS.get("test_mode"))})

    set_user_name()
    set_returned_granularities()    

    # / parameters & modifications #############################################

except Exception as e:
    if not "___shell___" in HTTP_HOST:
        print('Content-Type: text/plain')
        print('status: 302')
        print()
    
    print(logger.critical(f"Bycon initialization failed: {str(e)}"))
    print(traceback.format_exc())
    exit()


