from bycon import prdbug, prjsonhead, prjsontrue, BYC, BYC_PARS, BeaconErrorResponse, read_schema_file


def byconschemas():
    """
    This helper service reads and serves local schema definition files. The name of
    the schema (corresponding to the file name minus extension) is provided either
    as an `id` query parameter or as the first part of the path after `schemas/`.

    * <https://progenetix.org/services/schemas/biosample>
    """
    if (schema_name := BYC_PARS.get("id")):
        schema_name = schema_name.split('.').pop(0)
        if (s := read_schema_file(schema_name, "")):
            prjsonhead()
            prjsontrue(s)
            exit()
    
    BYC["ERRORS"].append("No correct schema id provided!")
    BeaconErrorResponse().respond_if_errors(422)
