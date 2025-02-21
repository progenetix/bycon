#!/usr/local/bin/python3

import traceback
from importlib import import_module

from bycon import (
    BYC,
    BYC_PARS,
    BeaconErrorResponse,
    prdbug,
    print_text_response
)

################################################################################
################################################################################
################################################################################

def main():
    try:
        services()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def services():
    """
    The `services` application deparses a request URI and calls the respective
    script. The functionality is combined with the correct configuration of a 
    rewrite in the server configuration for creation of canonical URLs.
    """
    rq_id = BYC.get("request_entity_id", "ids")
    rq_p_id = BYC.get("request_entity_path_id", "ids")
    rp_id = BYC.get("response_entity_id")

    # print('Content-Type: text')
    # print()
    # print(f'rq_id: {rq_id}, rq_p_id: {rq_p_id}, rp_id: {rp_id}')
    
    if not rp_id:
        pass
    elif rq_p_id:
        # dynamic package/function loading with function names equal to the module
        # names; e.g. `interval_frequencies` loads
        # `interval_frequencies` from `interval_frequencies.py`
        try:
            mod = import_module(rq_p_id)
            serv = getattr(mod, rq_p_id)
            serv()
            exit()
        except Exception as e:
            print('Content-Type: text')
            print('status:422')
            print()
            print(f'Service {rq_id} WTF error: {e}')

            exit()

    BYC["ERRORS"].append("No correct service path provided. Please refer to the documentation at http://bycon.progenetix.org")
    BeaconErrorResponse().respond_if_errors()


################################################################################
################################################################################

if __name__ == '__main__':
    main()
