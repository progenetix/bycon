#!/usr/bin/env python3
import cgi, cgitb, sys
from os import pardir, path

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""podmd

* <https://progenetix.org/beacon/info/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    info()
    
################################################################################

def info():

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
    info = object_instance_from_schema_name(byc, "beaconInfoResults", "properties", "json")

    for k in info.keys():
        if k in pgx_info:
            info.update({k:pgx_info[k]})

    r.update( {"response": info } )
    byc.update({"service_response": r, "error_response": e })

    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
