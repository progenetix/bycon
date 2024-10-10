from bycon import (
    BYC_PARS,
    BeaconDataResponse,
    print_json_response
)

def cnvstats():
    BYC_PARS.update({
        "output":"cnvstats",
        "include_handovers": False
    })
    rss = BeaconDataResponse().resultsetResponse()
    print_json_response(rss)

