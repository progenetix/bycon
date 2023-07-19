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

    b_e_d = byc["beacon_defaults"].get("entity_defaults", {})

    schema = {
        "entity_type": "info",
        "schema": "http://progenetix.org/services/schemas/beaconInfoResults"
    }

    r["meta"].update( { "returned_schemas": [ schema ] } )
    r["meta"].pop("received_request_summary", None)
    r["meta"].pop("returned_granularity", None)

    pgx_info = b_e_d.get("info", {})
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
