#!/usr/bin/env python3
import sys, traceback
from os import path, environ, pardir

from bycon import *

services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from export_file_generation import export_pgxseg_download

"""
The plot service uses the standard bycon data retrieval pipeline with `biosample`
as entity type. Therefore, all standard Beacon query parameters work and also
the path is interpreted for an biosample `id` value if there is an entry at
`.../pgxsegvariants/{id}`

* http://progenetix.org/services/pgxsegvariants/pgxbs-kftvjv8w

"""

################################################################################
################################################################################
################################################################################

def main():
    try:
        pgxsegvariants()
    except Exception:
        print_text_response(traceback.format_exc(), 302)


################################################################################

def pgxsegvariants():
    BYC.update({
        "request_entity_path_id": "biosamples",
        "request_entity_id": "biosample"
    })
    initialize_bycon_service()
    rss = ByconResultSets().datasetsResults()
    # TODO: multi-dataset?
    ds_id = list(rss.keys())[0]
    export_pgxseg_download(rss, ds_id)


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
