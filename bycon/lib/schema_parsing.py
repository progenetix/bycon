import re, json, yaml

from json_ref_dict import RefDict, materialize
from humps import decamelize
from os import path, scandir, pardir
from pathlib import Path

from cgi_parsing import prjsonnice

# local
lib_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( lib_path, pardir )

################################################################################

def read_schema_file(byc, schema_name, item, ext="json"):

    b_p_m = byc["beacon_mappings"]["default_schema_from_model"]

    schema_name = b_p_m.get(schema_name, schema_name)
    
    s_f_p = get_schema_file_path(byc, schema_name, ext)

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

def get_schema_file_path(byc, schema_name, ext="json"):

    e_l = f'.{ext}'
    d_n = f'defaultSchema.{ext}'
    s_n = f'{schema_name}.{ext}'

    p = Path(path.join( pkg_path, *byc["config"]["schemas_path"] ))
    s_p_s = [ f for f in p.rglob("*") if f.is_file() ]
    s_p_s = [ f for f in s_p_s if f.suffix == e_l ]

    for f_p in s_p_s:
        if f_p.parent.name == schema_name:
            if f_p.name == d_n:
                return f'{f_p.resolve()}'
        elif f_p.name == s_n:
            return f'{f_p.resolve()}'

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
    s_i = decamelize(s_i)
    return s_i

################################################################################

def object_instance_from_schema_name(byc, schema_name, root_key, ext="json"):
    s_f = read_schema_file(byc, schema_name, root_key, ext)
    s_i = create_empty_instance( s_f )

    return s_i

################################################################################
