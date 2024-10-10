from bycon import (
    BeaconErrorResponse,
    BYC,
    Cytobands,
    print_json_response
)
from byconServiceLibs import ByconServiceResponse

def cytomapper():
    if not (cbr := Cytobands().cytobands_response()):
        BYC["ERRORS"].append("No matching cytobands!")
        BeaconErrorResponse().respond_if_errors()

    print_json_response(ByconServiceResponse().populated_response([cbr]))
