#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
dir_path = path.dirname(path.abspath(__file__))
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import cgi_print_json_response
from bycon.lib.read_specs import dbstats_return_latest
from bycon.lib.parse_filters import select_dataset_ids, check_dataset_ids

service_lib_path = path.join( pkg_path, "services", "lib" )
sys.path.append( service_lib_path )

from service_utils import initialize_service, create_empty_service_response, populate_service_response, response_add_error,response_add_parameter,response_collect_errors,response_map_results

from byconeer.lib.schemas_parser import *


"""podmd

* <https://progenetix.org/beacon/info/>

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    info()
    
################################################################################

def info():

    byc = initialize_service()

    parse_beacon_schema(byc)

    r = create_empty_service_response(byc)

    r["meta"].update({
        "api_version": byc["beacon"]["info"]["version"],
    })

    stat = dbstats_return_latest(byc)[0]

    for ds_id, ds in byc["dataset_definitions"].items():
        if ds_id in stat["datasets"]:
            ds_vs = stat["datasets"][ds_id]
            if "counts" in ds_vs:
                if ds_vs["counts"]["variants"]:
                    ds["callCount"] = ds_vs["counts"]["variants"]
                if ds_vs["counts"]["variants_distinct"]:
                    ds["variantCount"] = ds_vs["counts"]["variants_distinct"]
                if ds_vs["counts"]["biosamples"]:
                    ds["sampleCount"] = ds_vs["counts"]["biosamples"]

        byc["beacon_info"]["datasets"].append(ds)

    populate_service_response( r, [ byc["beacon_info"] ] )
    cgi_print_json_response( byc[ "form_data" ], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
