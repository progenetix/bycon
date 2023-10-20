#!/usr/bin/env python3

from bycon import *

"""podmd

* <https://progenetix.org/beacon/filtering_terms>
* <https://cancercelllines.org/beacon/filtering_terms?collationTypes=cellosaurus>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        filtering_terms()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)

 
################################################################################

def filtering_terms():
    initialize_bycon_service(byc, "filtering_terms")
    run_beacon_init_stack(byc)

    r = BeaconDataResponse(byc)

    byc.update({
        "service_response": r.filteringTermsResponse(),
        "error_response": r.errorResponse()
    })

    cgi_print_response( byc, 200 )


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
