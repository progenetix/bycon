from os import environ, path, pardir
from pymongo import MongoClient
import sys
import socket

pkg_path = path.dirname( path.abspath(__file__) )

"""
Global variables
Potentially in th eenvironment:

DATABASE_NAMES
DB_MONGOHOST

"""

ENV = environ.get('HTTP_HOST', "___shell___")
HOSTNAME = environ.get('HOSTNAME', socket.gethostname())

PKG_PATH = pkg_path
CONF_PATH = path.join( pkg_path, "config")
LIB_PATH = path.join( pkg_path, "lib")

NO_PARAM_VALUES = ["none", "null", "undefined"]

# path of the calling script is used to point to a local config directory
CALLER_PATH = path.dirname( path.abspath(sys.argv[0]))
PROJECT_PATH = path.join(CALLER_PATH, pardir)
LOC_PATH = path.join(PROJECT_PATH, "local")

REQUEST_PATH_ROOT = "beacon"

if "services" in LOC_PATH or "byconaut" in LOC_PATH:
    REQUEST_PATH_ROOT = "services"

#------------------------------------------------------------------------------#
# Database settings
#------------------------------------------------------------------------------#

DB_MONGOHOST = environ.get("BYCON_MONGO_HOST", "localhost")

# TODO: wrap them into object to make them mutable for local changes
# or through environment variables like the host

HOUSEKEEPING_DB = "_byconHousekeepingDB"
HOUSEKEEPING_INFO_COLL = "beaconinfo"
HOUSEKEEPING_HO_COLL = "querybuffer"

SERVICES_DB = "_byconServicesDB"
GENES_COLL = "genes"
GEOLOCS_COLL = "geolocs"

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

  "beacon_defaults": {
    "defaults": {
      "default_dataset_id": "examplez",
      "test_domains": ["localhost"]
    },
  },

  # ..._mappings / ..._definitions are generated from YAML files & should stay static

  "argument_definitions": {"$defs":{}},
  "dataset_definitions": {},
  "datatable_mappings": {},
  "entity_defaults": {"info":{}},
  "filter_definitions": {"$defs":{}},
  "handover_definitions": {},
  "interval_definitions": {},
  "test_queries": {},
  "variant_request_definitions": {},
  "variant_type_definitions": {},

  "loc_mod_pars": [
    "argument_definitions",
    "authorizations",
    "dataset_definitions",
    "filter_definitions",
    "env_paths",
    "datatable_mappings",
    "test_queries",
    "plot_defaults"
  ],

  "authorizations": {},
  "env_paths": {},
  "plot_defaults": {},
  "request_meta": {},
  "service_config": {},

  # -------------------------------------------------------------------------- #

  "authorized_granularities": {},
  "request_entity_id": None,
  "response_entity_id": None,
  "response_entity": {},
  "response_schema": "beaconInfoResponse",
  "bycon_response_class": "BeaconInfoResponse",
  "returned_granularity": "boolean"
}

# collection object for cmd arguments and web parameters (depending on the ENV)
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
  "PATO",
  "pubmed"
]

################################################################################

