#!/usr/bin/env python3

from bycon import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        entry_types()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
    

################################################################################

def entry_types():

    initialize_bycon_service(byc, "entry_types")
    r = BeaconInfoResponse(byc)
    e_f = get_schema_file_path("beaconConfiguration")
    e_t_s = load_yaml_empty_fallback( e_f )
    print_json_response(r.populatedInfoResponse({"entry_types": e_t_s["entryTypes"] }))


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
