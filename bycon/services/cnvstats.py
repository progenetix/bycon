#!/usr/bin/env python3
import sys
from os import path, environ, pardir

from bycon import *

services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from interval_utils import generate_genome_bins

"""
The service uses the standard bycon data retrieval pipeline with `analysis`
as entity type. Therefore, all standard Beacon query parameters work and also
the path is interpreted for an biosample `id` value if there is an entry at
`.../analyses/{id}`
"""

################################################################################
################################################################################
################################################################################

def main():
    cnvstats()


################################################################################

def cnvstats():
    initialize_bycon_service()
    BYC_PARS.update({
        "output":"cnvstats",
        "include_handovers": False
    })
    rss = BeaconDataResponse().resultsetResponse()
    print_json_response(rss)


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
