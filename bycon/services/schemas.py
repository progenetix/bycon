#!/usr/bin/env python3
import sys, traceback
from os import path
from humps import camelize

from bycon import *

services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from service_helpers import *
from service_response_generation import *

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
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def schemas():
    initialize_bycon_service()
    r = ByconautServiceResponse()

    if "id" in BYC_PARS:
        schema_name = BYC_PARS.get("id")
    else:
        schema_name = BYC.get("request_entity_path_id_value")
        schema_name = schema_name[0]


    if schema_name:
        comps = schema_name.split('.')
        schema_name = comps.pop(0)
        s = read_schema_file(schema_name, "")
        if s:
            print('Content-Type: application/json')
            print('status:200')
            print()
            print(json.dumps(camelize(s), indent=4, sort_keys=True, default=str)+"\n")
            exit()

    BYC["ERRORS"].append("No correct schema id provided!")
    BeaconErrorResponse().response(422)


################################################################################
################################################################################

if __name__ == '__main__':
    main()
