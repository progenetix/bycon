#!/usr/bin/env python3

from os import path, pardir
import sys

from bycon import *

################################################################################
################################################################################
################################################################################

def main():

    try:
        configuration()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)    
    
################################################################################

def configuration():

    initialize_bycon_service(byc)
    r, e = instantiate_response_and_error(byc, "beaconConfigurationResponse")
    response_meta_set_info_defaults(r, byc)

    c_f = get_schema_file_path(byc, "beaconConfiguration")
    c = load_yaml_empty_fallback( c_f )

    r.update( {"response": c } )

    byc.update({"service_response": r, "error_response": e })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
