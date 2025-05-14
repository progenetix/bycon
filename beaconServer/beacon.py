#!/usr/local/bin/python3

from bycon import (
    BYC,
    BeaconDataResponse,
    BeaconErrorResponse,
    BeaconInfoResponse,
    prdbug,
    print_json_response
)

################################################################################

"""
The type of execution depends on the requested entity defined in the
`request_entity_path_id` (or aliases) in `entity_defaults`.
The entity is determined from different potential inputs and overwritten
by the next one in the order, if existing:

1. from the path (element after "beacon", e.g. `biosamples` from
   `/beacon/biosamples/...`)
2. from a form value, e.g. `?requestEntityPathId=biosamples`
3. from a command line argument, e.g. `--requestEntityPathId biosamples`

Fallback is `/info` - so the 422 shouldn't be a thing...
"""

BeaconErrorResponse().respond_if_errors()

b_r_c = BYC.get("bycon_response_class", "___none___")

r = None
if b_r_c == "BeaconInfoResponse":
    r = BeaconInfoResponse().populatedInfoResponse()
elif b_r_c == "BeaconDataResponse":
    r = BeaconDataResponse().dataResponseFromEntry()
BeaconErrorResponse().respond_if_errors()
if r:
    print_json_response(r)

BYC["ERRORS"].append("No correct service path provided. Please refer to the documentation at http://docs.progenetix.org")
BeaconErrorResponse().respond_if_errors()

