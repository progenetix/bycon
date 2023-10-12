#!/usr/bin/env python3

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
    r = object_instance_from_schema_name(byc, "beaconConfigurationResponse", "")
    e = object_instance_from_schema_name(byc, "beaconErrorResponse", "")
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
