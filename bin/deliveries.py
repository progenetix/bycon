#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path as path
from os import environ
import sys, os, datetime, argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""podmd

A simple app which only provides data deliveries from handover objects.

#### Required

* `accessid`

#### Optional

* `deliveryKeys`
  - list (can be comma-concatenated or multiple times parameter) to select the
  returned data fields

#### Examples

Examples here need a locally existing `accessid` parameter.

* <http://progenetix.org/services/deliveries?accessid=003d0488-0b79-4ffa-a38f-2fb932480eee&deliveryKeys=id,biocharacteristics>

podmd"""

################################################################################
################################################################################
################################################################################


def main():

    deliveries("deliveries")
    
################################################################################

def deliveries(service):
    
    config = read_bycon_config( path.abspath( dir_path ) )

    byc = {
        "config": config,
        "form_data": cgi_parse_query(),
        "errors": [ ],
        "warnings": [ ]
    }

    # response prototype
    r = config["response_object_schema"]

    if "accessid" in byc["form_data"]:
        access_id = byc["form_data"].getvalue("accessid")
        r["parameters"].update( { "accessid": access_id } )
    else:
        r["errors"].append( "No accessid parameter." )
        cgi_print_json_response( byc["form_data"], r, 422 )

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
