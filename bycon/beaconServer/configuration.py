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

    initialize_bycon_service(byc, "configuration")
    r = BeaconInfoResponse(byc)
    c_f = get_schema_file_path(byc, "beaconConfiguration")
    c = load_yaml_empty_fallback( c_f )

    byc.update({
        "service_response": r.populatedInfoResponse(c),
        "error_response": r.errorResponse()
    })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
