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

    populate_service_response( byc, return_filtering_terms(byc) )
    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################
################################################################################

def return_filtering_terms( byc ):

    fts = { }

    # for the general filter response, filters from *all* datasets are
    # provided
    # if only one => counts are added back

    for ds in byc[ "beacon_info" ][ "datasets" ]:
        if len(byc[ "dataset_ids" ]) > 0:
            if not ds["id"] in byc[ "dataset_ids" ]:
                continue
        if "filtering_terms" in ds:
            for f_t in ds[ "filtering_terms" ]:
                f_id = f_t[ "id" ]
                if not f_id in fts:
                    fts[ f_id ] = f_t
                else:
                    fts[ f_id ][ "count" ] += f_t[ "count" ]
  
    ftl = [ ]
    for key in sorted(fts):
        f_t = fts[key]
        if len(byc[ "dataset_ids" ]) > 1:
            del(f_t["count"])
        if "filters" in byc:
            if len(byc["filters"]) > 0:
                for f in byc["filters"]:
                    f_re = re.compile(r'^'+f)
                    if f_re.match(key):
                        ftl.append( f_t )
        else: 
            ftl.append( f_t )

    return ftl

################################################################################
################################################################################
################################################################################
   

if __name__ == '__main__':
    main()
