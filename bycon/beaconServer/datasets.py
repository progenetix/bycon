#!/usr/bin/env python3

from bycon import *

"""podmd

* <https://progenetix.org/beacon/datasets/>
* <https://progenetix.org/beacon/datasets/examplez/>
* <https://progenetix.org/beacon/datasets/?datasetIds=examplez,progenetix>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        datasets()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)


################################################################################

def datasets():

    initialize_bycon_service(byc)
    run_beacon_init_stack(byc)
    r = BeaconDataResponse(byc)
    byc.update({
        "service_response": r.collectionsResponse(),
        "error_response": r.errorResponse()
    })

    cgi_print_response( byc, 200 )


################################################################################
################################################################################

if __name__ == '__main__':
    main()
