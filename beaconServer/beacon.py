#!/usr/local/bin/python3

from bycon import (
    BYC,
    BeaconDataResponse,
    BeaconErrorResponse,
    BeaconInfoResponse,
    print_json_response,
    print_text_response
)

################################################################################

"""
The type of execution depends on the requested entity defined in the
`beacon_configuration` with the respective path retrieved from `beacon_map`.
The entity is determined from different potential inputs and overwritten
by the next one in the order, if existing:

1. from the path (element after "beacon", e.g. `biosamples` from
   `/beacon/biosamples/...`)
2. from a form value, e.g. `?requestEntityPathId=biosamples`
3. from a command line argument, e.g. `--requestEntityPathId biosamples`
    - short form argument is `-e biosamples`

Fallback is `/info` - so the 422 shouldn't be a thing...
"""
def main():

    # Initial error check
    BeaconErrorResponse().respond_if_errors()

    # Get response schema type
    b_r_s = BYC.get("response_schema", "beaconInfoResponse")

    # Determine response type and generate appropriate response
    if b_r_s in BYC.get("info_responses", []):
        r = BeaconInfoResponse().populatedInfoResponse()
    elif b_r_s in BYC.get("data_responses", []):
        r = BeaconDataResponse().dataResponseFromEntry()
    else:
        BYC["ERRORS"].append(f"Unsupported response schema type {b_r_s}")

    # Final error check before printing
    BeaconErrorResponse().respond_if_errors()

    if r:
        print_json_response(r)

    e_m = "No correct Beacon path provided. Please refer to the documentation at http://bycon.progenetix.org"
    BYC["ERRORS"].append(e_m)
    BeaconErrorResponse().respond_if_errors()

################################################################################

if __name__ == "__main__":
    main()
    
################################################################################