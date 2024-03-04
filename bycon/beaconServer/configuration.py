#!/usr/bin/env python3

from bycon import *

################################################################################
################################################################################
################################################################################

def main():
    try:
        configuration()
    except Exception:
        print_text_response(traceback.format_exc(), 302)    
    
################################################################################

def configuration():
    initialize_bycon_service(byc, "configuration")
    r = BeaconInfoResponse(byc)
    c_f = get_schema_file_path("beaconConfiguration")
    c = load_yaml_empty_fallback(c_f)
    print_json_response(r.populatedInfoResponse(c))


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
