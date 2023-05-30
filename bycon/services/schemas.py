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
        schemas()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)
    
################################################################################

def schemas():

    initialize_bycon_service(byc)
    create_empty_service_response(byc)

    if "id" in byc["form_data"]:
        schema_name = byc["form_data"].get("id", None)
    else:
        schema_name = rest_path_value("schemas")

    if schema_name is not None:

        comps = schema_name.split('.')
        schema_name = comps.pop(0)

        s = read_schema_file(schema_name, "", byc)
        if s is not False:

            print('Content-Type: application/json')
            print('status:200')
            print()
            print(json.dumps(camelize(s), indent=4, sort_keys=True, default=str)+"\n")
            exit()
    
    response_add_error(byc, 422, "No correct schema id provided!")
    cgi_print_response( byc, 422 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
