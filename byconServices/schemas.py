from bycon import prjsonhead, prjsontrue, BYC, BYC_PARS, BeaconErrorResponse, read_schema_file

"""podmd
* <https://progenetix.org/services/schemas/biosample>
podmd"""

def schemas():
    if not (schema_name := BYC_PARS.get("id")):
        if len(schema_name := BYC.get("request_entity_path_id_value", {})) > 0:
            schema_name = schema_name[0]
    if schema_name:
        schema_name = schema_name.split('.').pop(0)
        if (s := read_schema_file(schema_name, "")):
            prjsonhead()
            prjsontrue(s)
            exit()
    
    BYC["ERRORS"].append("No correct schema id provided!")
    BeaconErrorResponse().respond_if_errors(422)
