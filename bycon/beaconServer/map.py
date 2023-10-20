#!/usr/bin/env python3

from bycon import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        map()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)
    
################################################################################

def map():

    initialize_bycon_service(byc, "map")
    r = BeaconInfoResponse(byc)
    m_f = get_schema_file_path(byc, "beaconMap")
    beaconMap = load_yaml_empty_fallback( m_f )

    byc.update({
        "service_response": r.populatedInfoResponse(beaconMap),
        "error_response": r.errorResponse()
    })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
