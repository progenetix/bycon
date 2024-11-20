import inspect
from os import environ, path, pardir
from pymongo import MongoClient
import sys

pkg_path = path.dirname( path.abspath(__file__) )

"""
Global variables
"""

ENV = environ.get('HTTP_HOST', "___shell___")

PKG_PATH = pkg_path
CONF_PATH = path.join( pkg_path, "config")
LIB_PATH = path.join( pkg_path, "lib")

# path of the calling script is used to point to a local config directory
CALLER_PATH = path.dirname( path.abspath(sys.argv[0]))
LOC_PATH = path.join(CALLER_PATH, pardir, "local")

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

################################################################################
# to be modified during execution ##############################################
################################################################################

if "DATABASE_NAMES" in environ:
    db_names = environ["DATABASE_NAMES"].split()
else:
    mongo_client = MongoClient(host=DB_MONGOHOST)
    db_names = list(mongo_client.list_database_names())
    db_names = [x for x in db_names if x not in [HOUSEKEEPING_DB, SERVICES_DB, "admin", "config", "local"]]

BYC = {
  "DEBUG_MODE": False,
  "TEST_MODE": False,
  "ERRORS": [],
  "WARNINGS": [],
  "USER": "anonymous",

  "BYC_DATASET_IDS": [],
  "DATABASE_NAMES": db_names,
  "BYC_FILTERS": [],

  "beacon_defaults": {
    "defaults": {
      "default_dataset_id": "examplez",
      "test_domains": ["localhost"]
    },
  },

  # ..._mappings / ..._definitions are generated from YAML files & should stay static

  "argument_definitions": {},
  "dataset_definitions": {},
  "datatable_mappings": {},
  "entity_defaults": {"info":{}},
  "filter_definitions": {},
  "geoloc_definitions": {},
  "handover_definitions": {},
  "interval_definitions": {},
  "variant_request_definitions": {},
  "variant_type_definitions": {},

  "loc_mod_pars": [
    "authorizations",
    "dataset_definitions",
    "local_paths",
    "datatable_mappings",
    "plot_defaults"
  ],

  "authorizations": {},
  "local_paths": {},
  "plot_defaults": {},
  "query_meta": {},
  "service_config": {},

  # -------------------------------------------------------------------------- #

  "authorized_granularities": {},
  "parsed_config_paths": [],
  "request_entity_path_id": None,
  "request_entity_id": None,
  "response_entity_path_id": None,
  "response_entity_id": None,
  "response_entity": {},
  "response_schema": "beaconInfoResponse",
  "bycon_response_class": "BeaconInfoResponse",
  "path_id_value_bycon_parameter": None,
  "returned_granularity": "boolean"
}

# collection object for cmd arguments and web parameters (depending on the ENV)
# all possible parameters rare defined in `argument_definitions.yaml`, partially
# provifding default values
BYC_PARS = {}

# objects to make global, pre-processed variant parameters accessible
BYC_VARGS = {}

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
  "PMID"
]

################################################################################

