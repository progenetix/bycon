#!/usr/bin/env python3

from bycon import *

"""podmd

* <https://beacon.progenetix.org/beacon/filteringTerms

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

def filteringTerms():
    
    try:
        filtering_terms()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)

################################################################################

def filtering_terms():
    initialize_bycon_service(byc, "filtering_terms")
    run_beacon_init_stack(byc)
    select_dataset_ids(byc)
    return_filtering_terms_response(byc)


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
