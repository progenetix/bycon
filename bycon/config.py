import inspect
from os import environ, path, pardir

pkg_path = path.dirname( path.abspath(__file__) )

"""
Global variables
"""

ENV = environ.get('HTTP_HOST', "local")

PKG_PATH = pkg_path
CONF_PATH = path.join( pkg_path, "definitions")
LIB_PATH = path.join( pkg_path, "lib")

# path of the calling script is used to point to a local config directory
__caller_path = path.dirname(path.abspath((inspect.stack()[1])[1]))
LOC_PATH = path.join(__caller_path, "local")

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

BYC = {
  "DEBUG_MODE": False,
  "TEST_MODE": False,
  "ERRORS": [],
  "WARNINGS": [],
  "USER": "anonymous",
  "beacon_defaults": {
    "defaults": {
      "default_dataset_id": "examplez",
      "test_domains": ["localhost"]
    },
  },
  "entity_defaults": {"info":{}},
  "path_entry_type_mappings": {},
  "entry_type_path_mappings": {},
  "data_pipeline_entities": [],
  "datatable_mappings": {}
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

################################################################################

