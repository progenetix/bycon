from os import path

from bycon import (
    PKG_PATH,
    load_yaml_empty_fallback,
    prdbug,
    prjsonhead,
    prjsontrue,
    rest_path_value
)

"""podmd
The service provides the schemas for the `BeaconMap` OpenAPI endpoints.
* <https://progenetix.org/services/endpoints/analyses>
podmd"""

def endpoints():
    # TODO: This needs some error fallback, test for existing entities etc.
    schema_name = rest_path_value("endpoints")
    if schema_name:
        p = path.join( PKG_PATH, "schemas", "models", "src", "bycon-model", schema_name, "endpoints.yaml")
    else:
        p = path.join( PKG_PATH, "schemas", "models", "src", "bycon-model", "endpoints.yaml")

    prjsonhead()
    prjsontrue(load_yaml_empty_fallback(p))
    exit()
