#!/usr/local/bin/python3

import cgi, cgitb
import re, json, yaml
from os import path, environ, pardir
import sys, datetime, argparse
from pymongo import MongoClient

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from bycon.lib import *
from lib import *

"""podmd
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    collations()
    
################################################################################

def collations():

    byc = initialize_service("collations")

    select_dataset_ids(byc)
    parse_filters(byc)

    r = create_empty_service_response(byc)    

    if len(byc[ "dataset_ids" ]) < 1:
      response_add_error(r, 422, "No `datasetIds` parameter provided." )
 
    cgi_break_on_errors(r, byc)

    # data retrieval & response population
    s_s = { }
    d_k = response_set_delivery_keys(byc)

    mongo_client = MongoClient( )
    for ds_id in byc[ "dataset_ids" ]:
        mongo_db = mongo_client[ ds_id ]
        for f in byc[ "filters" ]:
            query = { "id": re.compile(r'^'+f ) }
            pre = re.split('-|:', f)[0]
            c = "collations"
            mongo_coll = mongo_db[ c ]
            for subset in mongo_coll.find( query ):

                if "codematches" in byc["method"]:
                    if not "code_matches" in subset:
                        continue
                    if int(subset[ "code_matches" ]) < 1:
                        continue

                i_d = subset["id"]
                if not i_d in s_s:
                    s_s[ i_d ] = { }
                for k in d_k:
                    # TODO: integer format defined in config?
                    if k in subset.keys():
                        if k == "count" or k == "code_matches":
                            if k in s_s[ i_d ]:
                                s_s[ i_d ][ k ] += int(subset[ k ])
                            else:
                                s_s[ i_d ][ k ] = int(subset[ k ])
                        else:
                            s_s[ i_d ][ k ] = subset[ k ]
                    else:
                        continue
                        # s_s[ i_d ][ k ] = None

    mongo_client.close( )

    populate_service_response(r, response_map_results( list(s_s.values()), byc))
    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
