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
    `path_entry_type_mappings` generated from `request_entity_path_id` (or aliases)
    in `entity_defaults`.
    The entity is determined from different potential inputs and overwritten
    by the next one in the order, if existing:

    1. from the path (element after "beacon", e.g. `biosamples` from
       `/beacon/biosamples/...`)
    2. from a form value, e.g. `?requestEntityPathId=biosamples`
    3. from a command line argument, e.g. `--requestEntityPathId biosamples`

    Fallback is `/info`.
    """
    
    p_e_m = BYC.get("path_entry_type_mappings", {})
    e_p_m = BYC.get("entry_type_path_mappings", {})
    d_p_e = BYC.get("data_pipeline_entities", [])
    byc.update({"request_path_root": "beacon"})
    rest_path_elements(byc)

    e_p_id = BYC_PARS.get("request_entity_path_id", "___none___")
    if e_p_id in p_e_m:
        byc.update({"request_entity_path_id": e_p_id})
    r_p_id = byc.get("request_entity_path_id", "info")
    prdbug(f'beacon.py - request_entity_path_id: {r_p_id}')

    e = p_e_m.get(r_p_id)
    f = e_p_m.get(e)

    if not f:
        pass
    elif e in d_p_e:
        initialize_bycon_service(byc, f)
        r = BeaconDataResponse(byc).resultsetResponse()
        print_json_response(r)
    elif f:
        # dynamic package/function loading; e.g. `filtering_terms` loads
        # `filtering_terms` from `filtering_terms.py`...
        try:
            mod = import_module(f)
            serv = getattr(mod, f)
            serv()
            exit()
        except Exception as e:
            print('Content-Type: text')
            print('status:422')
            print()
            print('Service {} WTF error: {}'.format(f, e))

            exit()

    BYC["ERRORS"].append("No correct service path provided. Please refer to the documentation at http://docs.progenetix.org")
    BeaconErrorResponse(byc).response(422)


################################################################################
################################################################################

if __name__ == '__main__':
    main()
