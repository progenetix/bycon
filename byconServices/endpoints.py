from os import path

from bycon import (
    PKG_PATH,
    load_yaml_empty_fallback,
    prdbug,
    prjsonhead,
    prjsontrue,
    ByconParameters
)


def endpoints():
    """
    The service provides the schemas for the `BeaconMap` OpenAPI endpoints.

    #### Examples (using the Progenetix resource as endpoint):

    * <https://progenetix.org/services/endpoints/analyses>
    * <https://progenetix.org/services/endpoints/biosamples>
    """
    # TODO: This needs some error fallback, test for existing entities etc.
    if (schema_name := ByconParameters().rest_path_value("endpoints")):
        p = path.join( PKG_PATH, "schemas", "models", "src", "bycon-model", schema_name, "endpoints.yaml")
    else:
        p = path.join( PKG_PATH, "schemas", "models", "src", "bycon-model", "endpoints.yaml")

    prjsonhead()
    prjsontrue(load_yaml_empty_fallback(p))
    exit()
