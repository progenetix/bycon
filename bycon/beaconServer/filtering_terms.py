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
        print_text_response(traceback.format_exc(), 302)

 
################################################################################

def filtering_terms():
    initialize_bycon_service(byc, "filtering_terms")
    r = BeaconDataResponse(byc)
    print_json_response(r.filteringTermsResponse())


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
