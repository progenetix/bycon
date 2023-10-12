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

    r = object_instance_from_schema_name(byc, "beaconEntryTypesResponse", "")
    e = object_instance_from_schema_name(byc, "beaconErrorResponse", "")
    response_meta_set_info_defaults(r, byc)

    e_f = get_schema_file_path(byc, "beaconConfiguration")
    e_t_s = load_yaml_empty_fallback( e_f )

    r["response"].update( {"entry_types": e_t_s["entryTypes"] } )

    byc.update({"service_response": r, "error_response": e })

    cgi_print_response( byc, 200 )


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
