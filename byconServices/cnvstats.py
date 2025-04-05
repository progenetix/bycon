from bycon import (
    BYC,
    BYC_PARS,
    BeaconDataResponse,
    print_json_response
)

def cnvstats():
    """
    ==TBD==
    """
    BYC_PARS.update({
        "output":"cnvstats",
        "include_handovers": False
    })
    rss = BeaconDataResponse().resultsetResponse()
    print_json_response(rss)

