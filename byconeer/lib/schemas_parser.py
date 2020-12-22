import re, json, yaml
from os import path, scandir
from json_ref_dict import RefDict, materialize

################################################################################

def read_schema_files(schema_root, item, dir_path):

    s_path = path.join( dir_path, "config", "schemas", schema_root+".yaml#/"+item )

    root_def = RefDict(s_path)

    exclude_keys = [ "format", "examples", "description" ]

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
        
    else:
        for k, val in schema.items():
        
            if isinstance(val, dict):
                schema[k] = instantiate_schema(val)
                
    return schema
        
################################################################################

def create_empty_instance(schema, dir_path):
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

def camel_to_pascal(name):

    return name.capitalize()
