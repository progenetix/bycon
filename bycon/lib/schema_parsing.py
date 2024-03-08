import humps, re, json

from json_ref_dict import RefDict, materialize
from os import path, scandir, pardir
from pathlib import Path

from bycon_helpers import prjsonnice, prdbug
from config import *

################################################################################

def read_schema_file(schema_name, item, ext="json"):
    # some lookup for the `request_entity_path_id` value in the case of "true"
    # entry types where schemas are defined in a directory with the path id
    b_e_d = BYC.get("entity_defaults", {})
    if schema_name in b_e_d:
        r_p_id = b_e_d[schema_name].get("request_entity_path_id")
        if isinstance(r_p_id, str):
            schema_name = r_p_id

    s_f_p = get_default_schema_file_path(schema_name, "defaultSchema", ext)
    if s_f_p is False:  # in case the name had been used as request_entity_path_id
        s_f_p = get_schema_file_path(schema_name, ext)

    if s_f_p is not False:
        if len(item) > 1:
            s_f_p = s_f_p+"#/"+item
        root_def = RefDict(s_f_p)
        
        exclude_keys = [ "examples" ] #"format",
        s = materialize(root_def, exclude_keys=exclude_keys)
        assert isinstance(s, dict)
        return s

    return False


################################################################################

def get_schema_file_path(schema_name, ext="json"):
    f_n = f'{schema_name}.{ext}'
    p = Path(path.join( PKG_PATH, "schemas" ))
    s_p_s = [ f for f in p.rglob("*") if f.is_file() ]
    s_p_s = [ f for f in s_p_s if f.name == f_n ]
    if len(s_p_s) == 1:
        return f'{s_p_s[0].resolve()}'

    return False


################################################################################

def get_default_schema_file_path(schema_path_id, file_name, ext="json"):
    f_n = f'{file_name}.{ext}'
    p = Path(path.join( PKG_PATH, "schemas" ))
    s_p_s = [ f for f in p.rglob("*") if f.is_file() ]
    s_p_s = [ f for f in s_p_s if f.name == f_n ]
    s_p_s = [ f for f in s_p_s if f.parent.name == schema_path_id ]
    if len(s_p_s) == 1:
        return f'{s_p_s[0].resolve()}'

    return False


################################################################################

def instantiate_schema(schema):
    if 'type' in schema:
        if schema['type'] == 'object' and 'properties' in schema:
            empty_dict = {}
            for prop, prop_schema in schema['properties'].items():
                empty_dict[prop] = instantiate_schema(prop_schema)
            return empty_dict
        elif schema['type'] == 'array' and 'items' in schema:
            return [instantiate_schema(schema['items'])]
        elif "const" in schema:
            return schema.get("const", "")
        elif "default" in schema:
            return schema["default"]

    return None
  

################################################################################

def create_empty_instance(schema):
    s_i = instantiate_schema(schema)
    s_i = humps.decamelize(s_i)
    return s_i


################################################################################

def object_instance_from_schema_name(schema_name, root_key, ext="json"):
    s_f = read_schema_file(schema_name, root_key, ext)
    s_i = create_empty_instance(s_f)

    return s_i


################################################################################
