#!/usr/bin/env python3
import re, sys, traceback
from os import path, environ
from importlib import import_module

from bycon import *

pkg_path = path.dirname( path.abspath(__file__) )

services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from service_helpers import read_service_prefs

"""
The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration for creation of canonical URLs.
"""

################################################################################
################################################################################
################################################################################

def main():
    try:
        services()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def services():
    set_debug_state(debug=0)

    rq_id = BYC.get("request_entity_id", "ids")
    rq_p_id = BYC.get("request_entity_path_id", "ids")
    rp_id = BYC.get("response_entity_id")

    if not rp_id:
        pass
    elif rq_p_id:
        # dynamic package/function loading; e.g. `intervalFrequencies` loads
        # `intervalFrequencies` from `interval_frequencies.py` which is an alias to
        # the `interval_frequencies` function there...
        try:
            mod = import_module(rq_p_id)
            serv = getattr(mod, rq_p_id)
            serv()
            exit()
        except Exception as e:
            print('Content-Type: text')
            print('status:422')
            print()
            print(f'Service {rq_id} WTF error: {e}')

            exit()

    BYC["ERRORS"].append("No correct service path provided. Please refer to the documentation at http://docs.progenetix.org")
    BeaconErrorResponse().response(422)


################################################################################
################################################################################

if __name__ == '__main__':
    main()
