#!/usr/local/bin/python3
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

    initialize_service(byc)

    pgx_info = byc["beacon_defaults"].get("info", {})
    info = object_instance_from_schema_name(byc, "ga4gh-service-info-1-0-0-schema", "properties", "json")

    for k in info.keys():
        if k in pgx_info:
            info.update({k:pgx_info[k]})
    print_json_response( info, byc["env"], 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()