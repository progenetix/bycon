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
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def cohorts():
    initialize_bycon_service(byc, "cohorts")
    r = BeaconDataResponse(byc).collectionsResponse()
    print_json_response(r)


################################################################################
################################################################################

if __name__ == '__main__':
    main()
