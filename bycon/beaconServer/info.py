#!/usr/bin/env python3
import cgi, sys
from os import pardir, path

from bycon import *

"""podmd

* <https://progenetix.org/beacon/info/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        info()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)
    
################################################################################

def info():

    initialize_bycon_service(byc)
    r, e = instantiate_response_and_error(byc, "beaconInfoResponse")
    response_meta_set_info_defaults(r, byc)

    beacon_schemas = []
    b_e_d = byc["beacon_defaults"].get("entity_defaults", {})
    for e_t, e_d in b_e_d.items():
        b_s = e_d.get("beacon_schema", {})
        if e_d.get("is_entry_type", True) is True:
            beacon_schemas.append(b_s)
    r["meta"].update( { "returned_schemas": beacon_schemas } )
    r["meta"].pop("test_mode", None)

    info = b_e_d.get("info", {})
    pgx_info = info.get("content", {})
    beacon_info = object_instance_from_schema_name(byc, "beaconInfoResults", "")
    for k in beacon_info.keys():
        if k in pgx_info:
            beacon_info.update({k:pgx_info[k]})

    r.update( {"response": beacon_info } )
    byc.update({"service_response": r, "error_response": e })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
