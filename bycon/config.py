from os import environ, path, pardir
from pymongo import MongoClient
import sys
import socket

pkg_path = path.dirname( path.abspath(__file__) )

"""
Runtime global variables that might be modified through providing them
in the environment:

DATABASE_NAMES
BYCON_MONGO_HOST
BYC_LOCAL_CONF ==> LOC_PATH

"""

HTTP_HOST = environ.get('HTTP_HOST', "___shell___")
HOSTNAME = environ.get('HOSTNAME', socket.gethostname())
REQUEST_SCHEME = environ.get('REQUEST_SCHEME', "___shell___")

BEACON_ROOT = f"{REQUEST_SCHEME}://{HTTP_HOST}"
if HTTP_HOST == "___shell___":
    BEACON_ROOT = f"cli://{HOSTNAME}"

PKG_PATH = pkg_path
CONF_PATH = path.join(pkg_path, "config")
LIB_PATH = path.join(pkg_path, "lib")

NO_PARAM_VALUES = ["none", "null", "undefined"]

# path of the calling script is used to point to a local config directory
CALLER_PATH = path.dirname( path.abspath(sys.argv[0]))
PROJECT_PATH = path.join(CALLER_PATH, pardir)

# local dataset configurations etc.
LOC_PATH = environ.get('BYC_LOCAL_CONF', path.join(PROJECT_PATH, "local"))

REQUEST_PATH_ROOT = "beacon"
if "services" in PROJECT_PATH:
    REQUEST_PATH_ROOT = "services"

#------------------------------------------------------------------------------#
# Database settings
#------------------------------------------------------------------------------#

BYC_DBS = {
  "mongodb_host": environ.get("BYCON_MONGO_HOST", "localhost"),
  "housekeeping_db": "_byconHousekeepingDB",
  "services_db": "_byconServicesDB",
  "info_coll": "beaconinfo",
  "handover_coll": "querybuffer",
  "genes_coll": "genes",
  "geolocs_coll": "geolocs",
  "genomicVariant_coll": "variants",
  "biosample_coll": "biosamples",
  "individual_coll": "individuals",
  "analysis_coll": "analyses",
  "run_coll": "analyses",
  "phenopacket_coll": "individuals",
  "filteringTerm_coll": "collations",
  "cohort_coll": "collations",
  "publication_coll": "publications"
}

MONGO_DISTINCT_STORAGE_LIMIT = 300000
VARIANTS_RESPONSE_LIMIT = 300000

################################################################################
# to be modified during execution ##############################################
################################################################################

errors = []

BYC = {
  "DEBUG_MODE": False,
  "TEST_MODE": False,
  "ERRORS": errors,
  "WARNINGS": [],
  "NOTES": [],
  "USER": "anonymous",

  "BYC_DATASET_IDS": [],

  "default_dataset_id": "examplez",
  "test_domains": ["localhost"],
 
  # ..._mappings / ..._definitions are generated from YAML files & should stay static

  "argument_definitions": {},
  "authorizations": {},
  "dataset_definitions": {},
  "datatable_mappings": {},
  "entity_defaults": {},
  "env_paths": {},
  "filter_definitions": {},
  "handover_definitions": {},
  "interval_definitions": {},
  "plot_defaults": {},
  "request_meta": {},
  "service_config": {},
  "test_queries": {},
  "variant_request_definitions": {},
  "variant_type_definitions": {},

  "loc_mod_pars": [
    "authorizations",
    "env_paths",
    "filter_definitions",
    "datatable_mappings",
    "test_queries",
    "plot_defaults"
  ],
  "info_responses": [
    "beaconInfoResponse" ,
    "beaconConfigurationResponse",
    "beaconMapResponse",
    "beaconEntryTypesResponse"
  ],
  "data_responses": [
    "beaconCollectionsResponse" ,
    "beaconResultsetsResponse",
    "beaconFilteringTermsResponse"
  ],


  # -------------------------------------------------------------------------- #

  "authorized_granularities": {},
  "request_entity_id": None,
  "response_entity_id": None,
  "response_entity": {},
  "response_schema": "beaconInfoResponse",
  "returned_granularity": "boolean"
}

# collection object for cmd arguments and web parameters (depending on the HTTP_HOST)
# all possible parameters rare defined in `argument_definitions.yaml`, partially
# provifding default values
BYC_PARS = {}

# default authorization levels; a local `authorizations.yaml` file can add to 
# these / override the values
# additionally to the default local `dataset_id` values can be added (as in 
# "examplez" here)
AUTHORIZATIONS = {
  "anonymous": {
    "default": "boolean",
    "examplez": "record"
  },
  "local": {"default": "record"}
}

#------------------------------------------------------------------------------#
# not really to be modified...
#------------------------------------------------------------------------------#

GRANULARITY_LEVELS = {
  "none": 0,
  "boolean": 1,
  "count": 2,
  "record": 3
}

BYC_UNCAMELED = [
  "gVariants",
  "gVariant",
  "sequenceId",
  "relativeCopyClass",
  "speciesId",
  "chromosomeLocation",
  "genomicLocation"
]

BYC_UPPER = [
  "EFO",
  "UBERON",
  "NCIT",
  "PATO"
]

################################################################################

