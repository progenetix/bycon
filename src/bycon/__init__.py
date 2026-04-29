# __init__.py

import socket
import sys
import logging
import traceback

from deepmerge import always_merger
from os import environ, pardir, path, scandir
from pathlib import Path

"""
bycon package initialization module.

Handles:
- Path configuration
- Module imports
- Configuration loading
- Parameter processing

Runtime global variables that might be modified through providing them
in the environment:

DATABASE_NAMES
BYCON_MONGO_HOST
BYC_LOCAL_CONF ==> LOC_PATH
"""

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

################################################################################
# BASE CONFIG & GLOBALS ########################################################
################################################################################

BEACON_API_VERSION = "v2.3.0-beaconplus"

PKG_PATH = path.dirname(path.abspath(__file__))
CONF_PATH = path.join(PKG_PATH, "config")
LIB_PATH = path.join(PKG_PATH)

# path of the calling script is used to point to a local config directory
CALLER_PATH = path.dirname(path.abspath(sys.argv[0]))
PROJECT_PATH = path.join(CALLER_PATH, pardir)
# local dataset configurations etc.
LOC_PATH = environ.get("BYC_LOCAL_CONF", path.join(PROJECT_PATH, "local"))

# ------------------------------------------------------------------------------#
# Web settings
# ------------------------------------------------------------------------------#

HOSTNAME = environ.get("HOSTNAME", socket.gethostname())
REQUEST_SCHEME = environ.get("REQUEST_SCHEME", "___shell___")
REQUEST_URI = environ.get("REQUEST_URI", False)
REQUEST_METHOD = environ.get("REQUEST_METHOD", "")
SCRIPT_URI = environ.get("SCRIPT_URI", "")
HTTP_HOST = environ.get("HTTP_HOST", "___shell___")
X_FORWARDED_PROTO = str(environ.get("HTTP_X_FORWARDED_PROTO"))

BEACON_ROOT = f"{REQUEST_SCHEME}://{HTTP_HOST}"
if "https" not in BEACON_ROOT and "https" not in X_FORWARDED_PROTO:
    BEACON_ROOT = BEACON_ROOT.replace("https://", "http://")
if HTTP_HOST == "___shell___":
    BEACON_ROOT = f"cli://{HOSTNAME}"

REQUEST_PATH_ROOT = "beacon"
if "services" in PROJECT_PATH:
    REQUEST_PATH_ROOT = "services"

# collection object for cmd arguments and web parameters (depending on the HTTP_HOST)
# all possible parameters rare defined in `argument_definitions.yaml`, partially
# provifding default values
BYC_PARS = {}

# path elements after the `beacon` or `services` REQUEST_PATH_ROOT
# .../{REQUEST_PATH_ROOT}/{request_entity_path_id}/  {path_ids}   /{response_entity_path_id}
# .../       beacon      /      individuals       /pgxind-kftx25eh/      biosamples
REQUEST_PATH_PARAMS = ["request_entity_path_id", "path_ids", "response_entity_path_id"]

# globals for treating "Null" value versions (e.g. from JS frontend to parameter
# to stack interpretation); tests are performed in a case-insensitive
PARAM_NONE_VALUES = ["none", "null", "undefined"]

# ------------------------------------------------------------------------------#
# Database settings
# ------------------------------------------------------------------------------#

BYC_DBS = {
    "mongodb_host": environ.get("BYCON_MONGO_HOST", "localhost"),
    "housekeeping_db": "_byconHousekeepingDB",
    "services_db": "_byconServicesDB",
    "collections": {
        "info": "beaconinfo",
        "handover": "querybuffer",
        "genes": "genes",
        "geolocs": "geolocs",
        "genomicVariant": "variants",
        "biosample": "biosamples",
        "individual": "individuals",
        "analysis": "analyses",
        "run": "analyses",
        "phenopacket": "individuals",
        "filteringTerm": "collations",
        "cohort": "collations",
        "collation": "collations",
        "publication": "publications",
        "analysis_cnv_map": "analyses_1Mb_maps",
        "analysis_gene_map": "analyses_genes_maps",
        "collation_cnv_map": "collations_1Mb_frequencymaps",
    },
}

# limits for MongoDB queries to avoid databasse errors
MONGO_DISTINCT_STORAGE_LIMIT = 300000
VARIANTS_RESPONSE_LIMIT = 300000

################################################################################
# potentially to be modified during execution ##################################
################################################################################

BYC = {
    "DEBUG_MODE": False,
    "TEST_MODE": False,
    "ERRORS": [],
    "WARNINGS": [],
    "NOTES": [],
    "USER": "anonymous",
    "BYC_DATASET_IDS": [],
    "default_dataset_id": "examplez",
    "test_domains": ["localhost"],
    "info_responses": [
        "beaconInfoResponse",
        "beaconConfigurationResponse",
        "beaconMapResponse",
        "beaconEntryTypesResponse",
    ],
    "data_responses": [
        "beaconCollectionsResponse",
        "beaconResultsetsResponse",
        "beaconAggregationConceptsResponse",
        "beaconFilteringTermsResponse",
    ],
    # ..._mappings / ..._definitions are generated from YAML files & should stay
    # static unless overridden by local defaults
    "aggregation_terms": {},
    "argument_definitions": {},
    "authorizations": {},
    "dataset_definitions": {},
    "datatable_mappings": {},
    "beacon_configuration": {},
    "env_paths": {},
    "filter_definitions": {},
    "handover_definitions": {},
    "genome_definitions": {},
    "geo_defaults": {},
    "plot_defaults": {},
    "request_profiles": {},
    "service_configuration": {},
    "test_queries": {},
    "variant_type_definitions": {},
    # parameter spaces for which local overrides are accepted
    # these are generated from the YAML files in `local`
    "loc_mod_pars": [
        "authorizations",
        "env_paths",
        "filter_definitions",
        "datatable_mappings",
        "test_queries",
        "plot_defaults",
    ],
    # -------------------------------------------------------------------------- #
    "authorized_granularities": {},
    "request_entity_id": None,
    "response_entity_id": None,
    "response_entity": {},
    "response_schema": "beaconInfoResponse",
    "returned_granularity": "boolean",
}

# default authorization levels; a local `authorizations.yaml` file can add to
# these / override the values
# additionally to the default local `dataset_id` values can be added (as in
# "examplez" here)
AUTHORIZATIONS = {
    "anonymous": {"default": "boolean", "examplez": "record"},
    "local": {"default": "record"},
}

# sorted granularities (least access to full)
GRANULARITIES = ["none", "boolean", "count", "aggregated", "record"]

# ------------------------------------------------------------------------------#
# not really to be modified...
# ------------------------------------------------------------------------------#

BYC_UNCAMELED = [
    "gVariants",
    "gVariant",
    "sequenceId",
    "relativeCopyClass",
    "speciesId",
    "chromosomeLocation",
    "genomicLocation",
]

BYC_UPPER = ["EFO", "UBERON", "NCIT", "PATO"]

################################################################################
# / BASE CONFIG & GLOBALS ######################################################
################################################################################

# try block to give at least some feedback on errors
# CAVE: bycon libraries depend on the configurations above and imports from them
# have to be defined *after* those variables
try:
    from .beacon_responses import BeaconErrorResponse, BeaconInfoResponse, BeaconDataResponse, ByconResultSets
    from .bycon_auth import ByconAuth
    from .bycon_helpers import (
        ByconError, ByconH, ByconID, ByconMongo, ByconTSVreader,
        dict_replace_values, get_nested_value, load_yaml_empty_fallback,
        print_json_response, print_yaml_response, print_text_response, print_html_response, print_uri_rewrite_response,
        prdlhead, prdbug, prjsonnice, prtexthead
    )
    from .bycon_info import ByconInfo
    from .bycon_summaries import ByconSummaries
    from .genome_utils import ChroNames, Cytobands, GeneInfo, GeneIntervals, VariantTypes
    from .parameter_parsing import ByconDatasets, ByconEntities, ByconFilters, ByconParameters, RefactoredValues
    from .query_execution import ByconDatasetResults
    from .query_generation import ByconQuery, CollationQuery, GeoQuery
    from .response_remapping import reshape_resultset_results
    from .schema_parsing import ByconSchemas, RecordsHierarchy
    from .variant_mapping import ByconVariant
    from .vrs_translator import AdjacencyTranslator, AlleleTranslator, CnvTranslator

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
                # logger.warning(f"Optional local config {local_file} not found")
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
    for e_k in list(b_e_t.keys()):
        b_e_t[e_k].update({"is_beacon_entity": True})
    s_e_t       = BYC.get("services_configuration", {}).get("entryTypes", {})
    e_d         = always_merger.merge(b_e_t, s_e_t)
 
    # modifying aliases in definitions with global variables
    for v in ["BEACON_ROOT", "BEACON_API_VERSION"]:
        if (r_v := globals().get(v)):
            e_d = dict_replace_values(e_d, f"___{v}___", r_v)

    # Mapping of entryTypes to endpoints using the default map
    endpoints   = BYC.get("beacon_map",     {}).get("endpointSets", {})
    services    = BYC.get("services_map",   {}).get("endpointSets", {})
    infos       = BYC.get("beacon_map",     {}).get("informationalEndpoints", {})

    for e in list(endpoints.values()) + list(infos.values()) + list(services.values()):
        if (e_id := e.get("entryType", "___none___")) not in e_d:
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
        if "___shell___" not in HTTP_HOST:
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

    ByconAuth()    

    # / parameters & modifications #############################################

except Exception as e:
    if "___shell___" not in HTTP_HOST:
        print('Content-Type: text/plain')
        print('status: 302')
        print()
    
    print(logger.critical(f"Bycon initialization failed: {str(e)}"))
    print(traceback.format_exc())
    exit()


