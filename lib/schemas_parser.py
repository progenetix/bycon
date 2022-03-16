import re, json, yaml
from os import path, scandir, pardir
from json_ref_dict import RefDict, materialize
import humps

# local
lib_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( lib_path, pardir )

################################################################################

def beacon_get_endpoint_base_paths(byc):

    try:
        p_s = byc["this_endpoints"]["paths"].keys()
    except:
        return byc

    r_p_bs = set()
    for p in p_s:
        p = re.sub(r'^\/',"", p )
        if len(p) > 1:
            r_p_bs.add( re.split('/', p)[0] )
    byc.update({"beacon_base_paths": list(r_p_bs) })

    return byc

################################################################################

def read_schema_file(schema_name, item, byc):

    s_f_p = get_schema_file_path(schema_name, byc)

    # print(schema_name, s_f_p)

    if not s_f_p is False:

        s_path = path.join( s_f_p, schema_name+".yaml#/"+item )
        root_def = RefDict(s_path)
        exclude_keys = [ "examples" ] #"format", 
        s = materialize(root_def, exclude_keys = exclude_keys)
        assert isinstance(s, dict)
        # print(s)
        return s

    return False

################################################################################

def get_schema_file_path(schema_name, byc):

    for s_p in byc["config"]["schema_paths"]:

        p = path.join( pkg_path, *s_p )
        s_fs = [ f.name for f in scandir(p) if f.is_file() ]
        s_fs = [ f for f in s_fs if f.endswith(".yaml") ]
        s_fs = [ f for f in s_fs if not f.startswith("_") ]

        for s_f in s_fs:

            f_name = path.splitext( s_f )[0]
            # print(schema_name, f_name)

            if f_name == schema_name:
                return p

    return False

################################################################################

def instantiate_schema(schema, is_root=True):

    if 'type' in schema.keys():

        if is_root is not True:

            t = schema['type']
        
            if t == 'array' or t == 'list':
                schema = []
            elif t == 'object':
                schema = { }
            elif t == 'integer':
                schema = int()
            elif t == 'number':
                schema = float()
            elif t == 'boolean':
                schema = False
            else:
                schema = ""
               
            return schema
      
    else:
        for k, val in schema.items():
            if isinstance(val, dict):
                schema.update({ k: instantiate_schema(val, False) })
                
    return schema
        
################################################################################

def create_empty_instance(schema):

    s_i = instantiate_schema(schema, True)
    s_i = humps.decamelize(s_i)
    return s_i

################################################################################

def object_instance_from_schema_name(byc, schema_name, root_key="properties"):

    s_i = create_empty_instance( read_schema_file(schema_name, root_key, byc) )
    return s_i

################################################################################

def convert_case_for_keys(schema_dict, convert_function):

    old_keys = list(schema_dict)

    for key in old_keys:
        new_key = convert_function(key)

        if type(schema_dict[key]) == dict:
            schema_dict[key] = convert_case_for_keys(schema_dict[key], convert_function)

        schema_dict[new_key] = schema_dict.pop(key)

    return schema_dict

################################################################################

def camel_to_snake(name):

    return humps.decamelize(name)

################################################################################

def snake_to_camel(name):

    return humps.camelize(name)

################################################################################

def camel_to_pascal(name):

    return name.capitalize( snake_to_camel(name) )
