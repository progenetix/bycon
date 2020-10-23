#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from pymongo import MongoClient
from bson.objectid import ObjectId
from os import path, environ, pardir
import sys, datetime, argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), pardir))
from bycon.lib.parse_filters import *
from bycon.lib.cgi_utils import *
from bycon.lib.handover_execution import retrieve_handover,handover_return_data
from bycon.lib.read_specs import read_local_prefs,read_named_prefs


"""podmd

A simple app which only provides data deliveries from handover objects.

#### Required

* `accessid` or
* `id` and `datasetId` and `collection` or
* `_id` and `datasetId` and `collection`

#### Optional

* `deliveryKeys`
  - list (can be comma-concatenated or multiple times parameter) to select the
  returned data fields

#### Examples

Examples here need a locally existing `accessid` parameter.

* <http://progenetix.org/services/deliveries?accessid=003d0488-0b79-4ffa-a38f-2fb932480eee&deliveryKeys=id,biocharacteristics>
* <https://progenetix.org/services/deliveries/?datasetIds=progenetix&collection=biosamples&id=pgxbs-kftva59y>
* https://progenetix.org/services/deliveries/?datasetIds=progenetix&collection=variants&_id=5bab576a727983b2e00b8d32>

podmd"""

################################################################################
################################################################################
################################################################################


def main():

    deliveries("deliveries")
    
################################################################################

def deliveries(service):

    byc = {
        "config": read_named_prefs( "defaults", dir_path ),
        "form_data": cgi_parse_query(),
        "errors": [ "No input parameter." ],
        "warnings": [ ]
    }

    these_prefs = read_local_prefs( "services", dir_path )

    # response prototype
    r = byc[ "config" ]["response_object_schema"]

    q_par = ""

    for p in ( "id", "_id", "accessid"):
        if p in  byc["form_data"]:
            v = byc["form_data"].getvalue( p )
            r["parameters"].update( { p: v } )
            r.update( { "errors": [ ] } )
            q_par = p

    if len(r["errors"]) > 0:
        cgi_print_json_response( byc["form_data"], r, 422 )

    # TODO: sub & clean upp etc.
    if not "accessid" in q_par:

        byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
        if not len(byc["dataset_ids"]) == 1:
            r["errors"].append( "Not exactly one datasetIds item specified." )
        else:
            ds_id = byc["dataset_ids"][0]
            if not ds_id in byc["config"]["dataset_ids"]:
                r["errors"].append( "Not exactly one datasetIds item specified." )

        if len(r["errors"]) > 0:
            cgi_print_json_response( byc["form_data"], r, 422 )

        if not "collection" in byc["form_data"]:
            r["errors"].append( "No data collection specified." )
            cgi_print_json_response( byc["form_data"], r, 422 )

        coll = byc["form_data"].getvalue( "collection" )
        if not coll in byc["config"]["collections"]:
            r["errors"].append( f"Collection {coll} is not specified in preferences." )
            cgi_print_json_response( byc["form_data"], r, 422 )

        q = { q_par: r["parameters"][ q_par ] }
        if "_id" in q_par:
            q = { "$or": [
                    { q_par: r["parameters"][ q_par ] },
                    { q_par: ObjectId( r["parameters"][ q_par ] ) }
                ] }

        mongo_client = MongoClient()
        r.update( { "data": mongo_client[ ds_id][ coll ].find_one( q ) } )
        mongo_client.close()

        r["parameters"].update( { "collection": coll } )
        r["parameters"].update( { "datasetId": ds_id } )
        r["response_type"] = coll
        if not r["data"]:
            r["errors"].append( "No data found under this {}: {}!".format(q_par, r["parameters"][ q_par ] ) )
            cgi_print_json_response( byc["form_data"], r, 422 )
        cgi_print_json_response( byc["form_data"], r, 200 )

    ############################################################################
    # continuing with default -> accessid
    ############################################################################

    access_id = r["parameters"][ q_par ]

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    d_k = form_return_listvalue( byc["form_data"], "deliveryKeys" )

    if e:
        r["errors"].append( e )
        cgi_print_json_response( byc["form_data"], r, 422 )

    r["parameters"].update( { "collection": h_o["target_collection"] } )
    r["parameters"].update( { "datasetId": h_o["source_db"] } )
    r["response_type"] = h_o["target_collection"]

    if len(d_k) > 0:
        for d in h_o_d:
            d_n = { }
            for k in d_k:
                if k in d:
                    d_n[ k ] = d[ k ]
            r["data"].append(d_n)
    else:
        r["data"] = h_o_d

    cgi_print_json_response( byc["form_data"], r, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
