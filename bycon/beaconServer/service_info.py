#!/usr/bin/env python3
import cgi, cgitb, sys
from os import pardir, path

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""podmd

* <https://progenetix.org/beacon/service-info/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    service_info()
    
################################################################################

def service_info():

    initialize_bycon_service(byc)

    defs = byc.get("beacon_defaults", {})
    b_e_d = defs.get("entity_defaults", {})
    pgx_info = b_e_d.get("info", {})
    info = object_instance_from_schema_name(byc, "ga4gh-service-info-1-0-0-schema", "properties", "json")

    for k in info.keys():
        if k in pgx_info:
            info.update({k:pgx_info[k]})
    print_json_response( info, byc["env"], 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()