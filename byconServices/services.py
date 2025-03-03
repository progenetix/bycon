#!/usr/local/bin/python3

from importlib import import_module, util

from bycon import (
    BYC,
    BeaconErrorResponse,
    prdbug
)

################################################################################

"""
The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration for creation of canonical URLs.
"""
rq_p_id = BYC.get("request_entity_path_id", "ids")

if not(servicemod := util.find_spec(rq_p_id)):
    BYC["ERRORS"].append(f'No correct service path provided through {servicemod}. Please refer to the documentation at http://bycon.progenetix.org')
    BeaconErrorResponse().respond_if_errors()

# dynamic package/function loading with function names equal to the module
# names; e.g. `interval_frequencies` loads
# `interval_frequencies` from `interval_frequencies.py`
try:
    mod = import_module(rq_p_id)
    serv = getattr(mod, rq_p_id)
    serv()
except Exception as e:
    BYC["ERRORS"].append(f"Service error: {e}")
    BeaconErrorResponse().respond_if_errors()
