from bycon import (
    BYC,
    BYC_PARS,
    prdbug,
    prjsonhead,
    prjsontrue,
    BeaconErrorResponse,
    ByconSchemas
)

def byconschemas():
    """
    This helper service reads and serves local schema definition files. The name of
    the schema (corresponding to the file name minus extension) is provided either
    as an `id` query parameter or as the first part of the path after `schemas/`.

    * <https://progenetix.org/services/schemas/biosample>
    """
    if (schema_name := BYC_PARS.get("id")):
        schema_name = schema_name.split('.').pop(0)
        if (s := ByconSchemas(schema_name, "").read_schema_file()):
            prjsonhead()
            prjsontrue(s)
            exit()
    
    BYC["ERRORS"].append("No correct schema id provided!")
    BeaconErrorResponse().respond_if_errors()
