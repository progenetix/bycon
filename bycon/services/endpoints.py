#!/usr/bin/env python3

import cgi
import re, json, yaml
from os import environ, pardir, path, scandir
import sys, datetime
from humps import camelize

from bycon import *

"""podmd

* <https://progenetix.org/services/schemas/biosample>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        endpoints()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)
    
################################################################################

def endpoints():

    initialize_bycon_service(byc)
    # create_empty_service_response(byc)

    schema_name = rest_path_value("endpoints")

    if schema_name is None:
        p = path.join( pkg_path, "schemas", "models", "json", "progenetix-model", "endpoints.json")
    else:
        comps = schema_name.split('.')
        schema_name = comps.pop(0)
        p = path.join( pkg_path, "schemas", "models", "json", "progenetix-model", schema_name, "endpoints.json")

    root_def = RefDict(p)
    exclude_keys = [ "format", "examples" ]
    s = materialize(root_def, exclude_keys = exclude_keys)

    if not s is False:

        print('Content-Type: application/json')
        print('status:200')
        print()
        print(json.dumps(camelize(s), indent=4, sort_keys=True, default=str)+"\n")
        exit()
    
################################################################################
################################################################################

if __name__ == '__main__':
    main()
