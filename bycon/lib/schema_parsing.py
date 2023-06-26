import re, json, yaml
from os import path, scandir, pardir
from json_ref_dict import RefDict, materialize
from humps import decamelize

from cgi_parsing import prjsonnice

# local
lib_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( lib_path, pardir )

################################################################################

def read_schema_file(schema_name, item, byc, ext="json"):

    b_p_m = byc["beacon_mappings"]["default_schema_from_model"]

    schema_name = b_p_m.get(schema_name, schema_name)
    
    s_f_p = get_schema_file_path(schema_name, byc, ext)

    # if byc["debug_mode"] is True:
    #     print(schema_name, s_f_p)

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

def get_schema_file_path(schema_name, byc, ext="json"):

    config = byc["config"]

    for s_p in config["schema_paths"]["items"]:

        p = path.join( pkg_path, *config["schemas_root"], *s_p )

        s_ds = [ d.name for d in scandir(p) if d.is_dir() ]
        if schema_name in s_ds:
            s_f_p = path.join( p, schema_name, "defaultSchema."+ext )
            return s_f_p

        s_fs = [ f.name for f in scandir(p) if f.is_file() ]
        s_fs = [ f for f in s_fs if f.endswith( ext ) ]
        s_fs = [ f for f in s_fs if not f.startswith("_") ]

        for s_f in s_fs:

            f_name = path.splitext( s_f )[0]
            # print(schema_name, f_name)

            if f_name == schema_name:
                s_f_p = path.join( p, s_f )
                return s_f_p

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
    s_f = read_schema_file(schema_name, root_key, byc, ext)
    s_i = create_empty_instance( s_f )

    return s_i

################################################################################
