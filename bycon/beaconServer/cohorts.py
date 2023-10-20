#!/usr/bin/env python3

from bycon import *

"""podmd

* <https://progenetix.org/beacon/cohorts/>
* <https://progenetix.org/beacon/cohorts/pgx:cohort-TCGA/>
* <https://progenetix.org/beacon/cohorts/?cohortIds=pgx:cohort-TCGA,pgx:cohort-oneKgenomes>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        cohorts()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)
    
################################################################################

def cohorts():

    initialize_bycon_service(byc, "cohorts")
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
