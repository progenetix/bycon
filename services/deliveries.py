#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from pymongo import MongoClient
from bson.objectid import ObjectId
from os import path, environ, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from beaconServer.lib.parse_filters import *
from beaconServer.lib.cgi_utils import *
from beaconServer.lib.handover_execution import retrieve_handover,handover_return_data
from beaconServer.lib.service_utils import *

"""podmd

* <https://progenetix.org/services/deliveries/?datasetIds=progenetix&collection=biosamples&id=pgxbs-kftva59y>

podmd"""

################################################################################
################################################################################
################################################################################


def main():

    deliveries()
    
################################################################################

def deliveries():

    byc = initialize_service()

    create_empty_service_response(byc)

    q_par = ""
    for p in byc["these_prefs"]["query_keys"]:
        if p in  byc["form_data"]:
            q_val = byc["form_data"].getvalue( p )
            response_add_parameter(byc, p, q_val)
            # last one is kept
            q_par = p

    # TODO: sub & clean upp etc.
    if not "accessid" in q_par:

        select_dataset_ids(byc)

        if not len(byc["dataset_ids"]) == 1:
            response_add_error(byc, 422, "Not exactly one datasetIds item specified." )
        else:
            ds_id = byc["dataset_ids"][0]
            if not ds_id in byc["dataset_definitions"]:
                response_add_error(byc, 422, "Not exactly one datasetIds item specified." )

        if not "collection" in byc["form_data"]:
            response_add_error(byc, 422, "No data collection specified." )

        cgi_break_on_errors(byc)

        coll = byc["form_data"].getvalue( "collection" )
        if not coll in byc["config"]["collections"]:
            response_add_error(byc, 422, f"Collection {coll} is not specified in preferences." )

        cgi_break_on_errors(byc)

        q = { q_par: q_val }
        if "_id" in q_par:
            q = { "$or": [
                    { q_par: q_val },
                    { q_par: ObjectId( q_val ) }
                ] }

        mongo_client = MongoClient()
        results = [ mongo_client[ ds_id][ coll ].find_one( q ) ]
        mongo_client.close()

        response_add_parameter(byc, "collection", coll )
        response_add_parameter(byc, "datasetId", ds_id )

        if not results or results[0] == None:
            response_add_error(byc, 422, "No data found under this {}: {}!".format(q_par, q_val) )

        cgi_break_on_errors(byc)
        populate_service_response( byc, results)
        cgi_print_json_response( byc, 200 )

    ############################################################################
    # continuing with default -> accessid
    ############################################################################

    access_id = q_par

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    d_k = form_return_listvalue( byc["form_data"], "deliveryKeys" )

    if e:
        response_add_error(byc, 422, e )

    response_add_parameter(byc, "collection", h_o["target_collection"] )
    response_add_parameter(byc, "datasetId", h_o["source_db"] )

    results = [ ]
    if len(d_k) > 0:
        for d in h_o_d:
            d_n = { }
            for k in d_k:
                if k in d:
                    d_n[ k ] = d[ k ]
            results.append(d_n)
    else:
        results = h_o_d

    populate_service_response( byc, results)
    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
