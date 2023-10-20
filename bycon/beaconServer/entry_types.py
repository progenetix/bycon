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
        print_text_response(traceback.format_exc(), byc["env"], 302)
    

################################################################################

def entry_types():

    initialize_bycon_service(byc, "entry_types")
    r = BeaconInfoResponse(byc)
    e_f = get_schema_file_path(byc, "beaconConfiguration")
    e_t_s = load_yaml_empty_fallback( e_f )

    byc.update({
        "service_response": r.populatedInfoResponse({"entry_types": e_t_s["entryTypes"] }),
        "error_response": r.errorResponse()
    })

    cgi_print_response( byc, 200 )


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
