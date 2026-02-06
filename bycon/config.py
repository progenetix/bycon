from os import environ, path, pardir
import sys
import socket

BEACON_API_VERSION  = "v2.2.2-beaconplus"

"""
Runtime global variables that might be modified through providing them
in the environment:

DATABASE_NAMES
BYCON_MONGO_HOST
BYC_LOCAL_CONF ==> LOC_PATH
"""

#------------------------------------------------------------------------------#
# Web settings
#------------------------------------------------------------------------------#

PKG_PATH            = path.dirname( path.abspath(__file__) )
CONF_PATH           = path.join(PKG_PATH, "config")
LIB_PATH            = path.join(PKG_PATH, "lib")

# path of the calling script is used to point to a local config directory
CALLER_PATH         = path.dirname( path.abspath(sys.argv[0]))
PROJECT_PATH        = path.join(CALLER_PATH, pardir)
# local dataset configurations etc.
LOC_PATH            = environ.get('BYC_LOCAL_CONF', path.join(PROJECT_PATH, "local"))

#------------------------------------------------------------------------------#
# Web settings
#------------------------------------------------------------------------------#

HOSTNAME            = environ.get('HOSTNAME', socket.gethostname())
REQUEST_SCHEME      = environ.get('REQUEST_SCHEME', "___shell___")
REQUEST_URI         = environ.get('REQUEST_URI', False)
REQUEST_METHOD      = environ.get('REQUEST_METHOD', '')
HTTP_HOST           = environ.get('HTTP_HOST', "___shell___")
BEACON_ROOT         = f"{REQUEST_SCHEME}://{HTTP_HOST}"
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
REQUEST_PATH_PARAMS = [
    "request_entity_path_id",
    "path_ids",
    "response_entity_path_id"
]

# globals for treating "Null" value versions (e.g. from JS frontend to parameter
# to stack interpretation)
PARAM_NONE_VALUES = ["none", "null", "undefined"]

#------------------------------------------------------------------------------#
# Database settings
#------------------------------------------------------------------------------#

BYC_DBS = {
    "mongodb_host": environ.get("BYCON_MONGO_HOST", "localhost"),
    "housekeeping_db": "_byconHousekeepingDB",
    "services_db": "_byconServicesDB",
    "collections": {
        "info":             "beaconinfo",
        "handover":         "querybuffer",
        "genes":            "genes",
        "geolocs":          "geolocs",
        "genomicVariant":   "variants",
        "biosample":        "biosamples",
        "individual":       "individuals",
        "analysis":         "analyses",
        "run":              "analyses",
        "phenopacket":      "individuals",
        "filteringTerm":    "collations",
        "cohort":           "collations",
        "collation":        "collations",
        "publication":      "publications"
    }
}

MONGO_DISTINCT_STORAGE_LIMIT    = 300000
VARIANTS_RESPONSE_LIMIT         = 300000

################################################################################
# potentially to be modified during execution ##################################
################################################################################

BYC = {
    "DEBUG_MODE":       False,
    "TEST_MODE":        False,
    "ERRORS":           [],
    "WARNINGS":         [],
    "NOTES":            [],
    "USER":             "anonymous",
    "BYC_DATASET_IDS":  [],

    "default_dataset_id": "examplez",
    "test_domains": [
        "localhost"
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
        "beaconAggregationConceptsResponse",
        "beaconFilteringTermsResponse"
    ],

    # ..._mappings / ..._definitions are generated from YAML files & should stay
    # static unless not overridden by local defaults

    "aggregation_terms":        {},
    "argument_definitions":     {},
    "authorizations":           {},
    "dataset_definitions":      {},
    "datatable_mappings":       {},
    "beacon_configuration":     {},
    "env_paths":                {},
    "filter_definitions":       {},
    "handover_definitions":     {},
    "interval_definitions":     {},
    "plot_defaults":            {},
    "request_profiles":         {},
    "service_configuration":    {},
    "test_queries":             {},
    "request_profiles":         {},
    "variant_type_definitions": {},

    "loc_mod_pars": [
        "authorizations",
        "env_paths",
        "filter_definitions",
        "datatable_mappings",
        "test_queries",
        "plot_defaults"
    ],


    # -------------------------------------------------------------------------- #

    "authorized_granularities": {},
    "request_entity_id":        None,
    "response_entity_id":       None,
    "response_entity":          {},
    "response_schema":          "beaconInfoResponse",
    "returned_granularity":     "boolean"
}

# default authorization levels; a local `authorizations.yaml` file can add to 
# these / override the values
# additionally to the default local `dataset_id` values can be added (as in 
# "examplez" here)
AUTHORIZATIONS = {
    "anonymous": {
        "default":  "boolean",
        "examplez": "record"
    },
    "local": {
        "default": "record"
    }
}

# integer granularities for some sorting of levels
GRANULARITY_LEVELS = {
  "none": 0,
  "boolean": 1,
  "count": 2,
  "aggregated": 3,
  "record": 4
}

#------------------------------------------------------------------------------#
# not really to be modified...
#------------------------------------------------------------------------------#

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

