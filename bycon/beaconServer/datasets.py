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
    initialize_bycon_service(byc, "datasets")
    run_beacon_init_stack(byc)
    r = BeaconDataResponse(byc)
    print_json_response(r.collectionsResponse(), byc["env"])


################################################################################
################################################################################

if __name__ == '__main__':
    main()
