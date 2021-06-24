#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import environ, pardir, path
import sys, os, datetime

# local
# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd

* <https://beacon.progenetix.org/beacon/filteringTerms

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    filtering_terms()
    
################################################################################

def filteringTerms():
    
    filtering_terms()

################################################################################

def filtering_terms():

    byc = initialize_service()

    parse_beacon_schema(byc)
    select_dataset_ids(byc)
    check_dataset_ids(byc)
    get_filter_flags(byc)
    parse_filters(byc)

    update_datasets_from_dbstats(byc)
    create_empty_service_response(byc)
    return_filtering_terms( byc )

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

def return_filtering_terms( byc ):

    fts = { }

    ft_fs = []
    if "filters" in byc:
        if len(byc["filters"]) > 0:
            for f in byc["filters"]:
                ft_fs.append('('+f+')')
    f_s = '|'.join(ft_fs)
    f_re = re.compile(r'^'+f_s)

    for ds in byc[ "beacon_info" ][ "datasets" ]:

        ds_id = ds["id"]

        if not ds_id in byc[ "dataset_ids" ]:
            continue

        # r_set = create_empty_instance(r_schema.copy())
        r_set = {
            "id": ds_id,
            "type": "dataset",
            "results_count": 0,
            "exists": False,
            "filtering_terms": [ ]
        }

        if "filtering_terms" in ds.keys():
            if len(ds[ "filtering_terms" ]) > 0:
                for f_t in ds[ "filtering_terms" ]:
                    if len(byc["filters"]) > 0:
                        if f_re.match(f_t[ "id" ]):
                            r_set["filtering_terms"].append(f_t)
                            fts.update({ f_t["id"]: f_t })
                    else:
                        r_set["filtering_terms"].append(f_t)
                        fts.update({ f_t["id"]: f_t })
        if len(r_set["filtering_terms"]) > 0:
            r_set.update({
                "filtering_terms": r_set["filtering_terms"],
                "results_count": len(r_set["filtering_terms"]),
                "exists": True
            })
            byc["service_response"]["response"]["exists"] = True

        byc["service_response"]["response"]["result_sets"].append(r_set)

    return byc

################################################################################
################################################################################
################################################################################
   

if __name__ == '__main__':
    main()
