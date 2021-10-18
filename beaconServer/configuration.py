#!/usr/local/bin/python3

from os import path, pardir
import sys

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    configuration()
    
################################################################################

def configuration():

    byc = initialize_service()
    create_empty_service_response(byc)

    # HOT FIX
    byc["service_response"].pop("info")
    byc["service_response"].pop("beacon_handovers")
    byc["service_response"].pop("response_summary")
    byc["service_response"]["meta"].pop("received_request_summary")

    byc["service_response"]["meta"].update({
        "info": "Progentix Beacon v2 configuration (transitional)",
        "returned_schemas": [
          {
            "configuration": "https://raw.githubusercontent.com/ga4gh-beacon/beacon-framework-v2/main/configuration/beaconConfigurationSchema.json"
          }
        ]
    })

    byc["service_response"].update({
        "$schema": "https://raw.githubusercontent.com/ga4gh-beacon/beacon-framework-v2/main/responses/beaconConfigurationResponse.json",
        "response": byc["beacon_configuration"],
     })


    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
