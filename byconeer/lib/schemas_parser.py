import re, json, yaml
from os import path, scandir, pardir
from json_ref_dict import RefDict, materialize
import sys

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )
schema_path = path.join( pkg_path, "bycon", "config", "schemas" )

################################################################################

def parse_beacon_schema(byc):

    bsp = path.join( schema_path, "beacon.yaml" )
    with open( bsp ) as bs:

        byc.update({ "beacon": yaml.load( bs , Loader=yaml.FullLoader) })

    return byc

################################################################################

def read_schema_files(schema_root, item, schema_path):


    s_path = path.join( schema_path, schema_root+".yaml#/"+item )
    # print(s_path)

    root_def = RefDict(s_path)

    exclude_keys = [ "format", "examples" ]

    return materialize(root_def, exclude_keys = exclude_keys)

################################################################################

def instantiate_schema(schema):

    if 'type' in schema.keys():

        t = schema['type']
    
        # # if schema['type'] == 'array' and 'items' in schema:
        # #     schema = [instantiate_schema(schema['items'])]
            
        # else:

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

    # elif 'properties' in schema.keys():
    #     for k, val in schema["properties"].items():
        
    #         if isinstance(val, dict):
    #             schema["properties"][k] = instantiate_schema(val)
      
    else:
        for k, val in schema.items():
        
            if isinstance(val, dict):
                schema[k] = instantiate_schema(val)
                
    return schema
        
################################################################################

def create_empty_instance(schema):
    s_convert = convert_case_for_keys(schema, camel_to_snake)
    return instantiate_schema(s_convert)

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

def snake_to_camel(name):

    comps = name.split('_')
    return comps[0] + ''.join(x.title() for x in comps[1:])

################################################################################

def camel_to_pascal(name):

    return name.capitalize()
