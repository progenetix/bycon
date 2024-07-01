#!/usr/bin/env python3

import sys, re
from deepmerge import always_merger
from os import path, pardir
from importlib import import_module

from bycon import *

"""
"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        beacon()
    except Exception:
        print_text_response(traceback.format_exc(), 302)

################################################################################

def beacon():
    """
    The type of execution depends on the requested entity defined in the
    `request_entity_path_id` (or aliases) in `entity_defaults`.
    The entity is determined from different potential inputs and overwritten
    by the next one in the order, if existing:

    1. from the path (element after "beacon", e.g. `biosamples` from
       `/beacon/biosamples/...`)
    2. from a form value, e.g. `?requestEntityPathId=biosamples`
    3. from a command line argument, e.g. `--requestEntityPathId biosamples`

    Fallback is `/info`.
    """
    
    d_p_e = BYC.get("data_pipeline_entities", [])
    rq_id = BYC.get("request_entity_id", "info")
    rq_p_id = BYC.get("request_entity_path_id", "info")
    rp_id = BYC.get("response_entity_id")

    if not rp_id:
        pass
    elif rq_id in d_p_e:
        r = BeaconDataResponse().resultsetResponse()
        print_json_response(r)
    elif rq_p_id:
        # dynamic package/function loading; e.g. `filtering_terms` loads
        # `filtering_terms` from `filtering_terms.py`...
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

    BYC["ERRORS"].append("No correct service path provided. Please refer to the documentation at http://docs.progenetix.org")
    BeaconErrorResponse().response(422)


################################################################################
################################################################################

if __name__ == '__main__':
    main()
