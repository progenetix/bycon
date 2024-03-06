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
    # updates `beacon_defaults`, `dataset_definitions` and `local_paths`
    # update_rootpars_from_local(LOC_PATH, byc)
    # set_beacon_defaults(byc)

    defs = BYC["beacon_defaults"]
    s_a_s = defs.get("service_path_aliases", {})
    r_w = defs.get("rewrites", {})
    d_p_s = defs.get("data_pipeline_path_ids", [])

    """
    The type of execution depends on the requested entity defined in `beacon_defaults`
    which can either be one of the Beacon entities (also recognizing aliases)
    in `beacon_defaults.service_path_aliases` or targets of a rewrite from
    `beacon_defaults.rewrites`.
    The entity is determined from different potential inputs and overwritten
    by the next one in the oreder, if existing:

    1. from the path (element after "beacon", e.g. `biosamples` from
       `/beacon/biosamples/...`)
    2. from a form value, e.g. `?requestEntityPathId=biosamples`
    3. from a command line argument, e.g. `--requestEntityPathId biosamples`

    Fallback is `/info`.
    """
    byc.update({"request_path_root": "beacon"})
    rest_path_elements(byc)
    # args_update_form(byc)
    prdbug(f'beacon.py - request_entity_path_id: {byc.get("request_entity_path_id")}')

    e_p_id = BYC_PARS.get("request_entity_path_id", "___none___")
    prdbug(f'beacon.py - form e_p_id: {e_p_id}')
    if e_p_id in s_a_s or e_p_id in r_w:
        byc.update({"request_entity_path_id": e_p_id})
    r_p_id = byc.get("request_entity_path_id", "info")

    prdbug(f'beacon.py - request_entity_path_id: {r_p_id}')

    # check for rewrites
    if r_p_id in r_w:
        uri = environ.get('REQUEST_URI')
        pat = re.compile( rf"^.+\/{r_p_id}\/?(.*?)$" )
        if pat.match(uri):
            stuff = pat.match(uri).group(1)
            print_uri_rewrite_response(r_w[r_p_id], stuff)

    f = s_a_s.get(r_p_id)
    if not f:
        pass
    elif f in d_p_s:
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
