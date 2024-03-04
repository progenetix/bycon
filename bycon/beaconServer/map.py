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
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def map():
    initialize_bycon_service(byc, "map")
    r = BeaconInfoResponse(byc)
    m_f = get_schema_file_path("beaconMap")
    beaconMap = load_yaml_empty_fallback( m_f )
    print_json_response(r.populatedInfoResponse(beaconMap))


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
