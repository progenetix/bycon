import re, json, yaml
from os import path, scandir
from json_ref_dict import RefDict, materialize

################################################################################

def read_schema_files(**byc):

    schemas = { }

    s_path = path.join( byc["pkg_path"], "byconeer", "config", "schemas", "Progenetix.yaml#/definitions" )

    root_def = RefDict(s_path)

    return materialize(root_def)

################################################################################

def create_db_schema(schemaname, **schemas):

    coll_s = { }

    s_n = camel_to_pascal(schemaname)
    s = schemas[ schemaname ]

    return {s_n: convert_case_for_keys(s, camel_to_snake)}

################################################################################

def convert_case_for_keys (schema_dict, convert_function):

    old_keys = list(schema_dict)

    for key in old_keys:
        new_key = convert_function(key)

        if type(schema_dict[key]) == dict:
            schema_dict[key] = convert_case_for_keys(schema_dict[key], convert_function)

        schema_dict[new_key] = schema_dict.pop(key)

    return schema_dict

################################################################################

def camel_to_snake(name):

    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

################################################################################

def camel_to_pascal(name):

    return name.capitalize()
