#!/usr/bin/env python3
import sys, traceback
from os import path

from bycon import *

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from service_helpers import read_service_prefs
from service_response_generation import *

"""podmd

* <https://progenetix.org/services/dbstats/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        dbstats()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
    
################################################################################

def dbstats():
    initialize_bycon_service()
    read_service_prefs("dbstats", services_conf_path)
    r = ByconautServiceResponse()

    stats = MongoClient(host=DB_MONGOHOST)[HOUSEKEEPING_DB][ HOUSEKEEPING_INFO_COLL ].find( { }, { "_id": 0 } ).sort( "date", -1 ).limit( 1 )

    results = [ ]
    for stat in stats:
        for ds_id, ds_vs in stat["datasets"].items():
            if len(BYC["BYC_DATASET_IDS"]) > 0:
                if not ds_id in BYC["BYC_DATASET_IDS"]:
                    continue
            dbs = { "dataset_id": ds_id }
            dbs.update({"counts":ds_vs["counts"]})
            results.append( dbs )

    print_json_response(r.populatedResponse(results))


################################################################################
################################################################################

if __name__ == '__main__':
    main()
