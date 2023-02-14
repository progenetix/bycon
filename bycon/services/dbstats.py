#!/usr/bin/env python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

"""podmd

* <https://progenetix.org/services/dbstats/>
* <https://progenetix.org/services/dbstats/?statsNumber=3&responseFormat=simple>
* <http://progenetix.org/cgi/bycon/services/dbstats.py?method=filtering_terms>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    dbstats()
    
################################################################################

def dbstats():

    initialize_bycon_service(byc)
    select_dataset_ids(byc)


    if "statsNumber" in byc["form_data"]:
        s_n = byc["form_data"]["stats_number"]
        try:
            s_n = int(s_n)
        except:
            pass
        if type(s_n) == int:
            if s_n > 0:
                byc["stats_number"] = s_n

    create_empty_service_response(byc)
    # exit()

    ds_stats = dbstats_return_latest(byc)

    results = [ ]
    for stat in ds_stats:
        # byc["service_response"]["info"].update({ "date": stat["date"] })
        for ds_id, ds_vs in stat["datasets"].items():
            if len(byc[ "dataset_ids" ]) > 0:
                if not ds_id in byc[ "dataset_ids" ]:
                    continue
            dbs = { "dataset_id": ds_id }
            dbs.update({"counts":ds_vs["counts"]})
            results.append( dbs )

    populate_service_response( byc, results )
    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
