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

from beaconServer.lib.cgi_utils import *
from beaconServer.lib.parse_filters import *
from beaconServer.lib.parse_variants import *
from beaconServer.lib.service_utils import *
from lib.cytoband_utils import *

################################################################################
################################################################################
################################################################################

def main():

    interval_frequencies()

################################################################################

def intervalFrequencies():
    interval_frequencies()
   
################################################################################

def interval_frequencies():

    byc = initialize_service()

    select_dataset_ids(byc)
    parse_filters(byc)
    parse_variants(byc)

    generate_genomic_intervals(byc)

    create_empty_service_response(byc)    

    if len(byc[ "dataset_ids" ]) < 1:
      response_add_error(byc, 422, "No `datasetIds` parameter provided." )
 
    cgi_break_on_errors(byc)

    if "id" in byc["form_data"]:
        byc[ "filters" ] = [ byc["form_data"].getvalue( "id" ) ]

    # data retrieval & response population
    c = byc["these_prefs"]["collection_name"]

    results = [ ]

    mongo_client = MongoClient( )
    for ds_id in byc[ "dataset_ids" ]:
        mongo_coll = mongo_client[ ds_id ][ c ]
        for f in byc[ "filters" ]:
            subset = mongo_coll.find_one( { "id": f } )
            if "codematches" in byc["method"]:
                if not "code_matches" in subset:
                    continue
                if int(subset[ "code_matches" ]) < 1:
                    continue

            i_d = subset["id"]
            r_o = { "dataset_id": ds_id, "id": i_d, "interval_frequencies": [ ] }
            for interval in byc["genomic_intervals"]:
                i = interval["index"]
                # TODO: Error if length ...
                r_o["interval_frequencies"].append( {
                    "index": i,
                    "chro": interval["chro"],
                    "start": interval["start"],
                    "end": interval["end"],
                    "gain_frequency": round(subset["frequencymaps"]["dupfrequencies"][i], 2),
                    "loss_frequency": round(subset["frequencymaps"]["delfrequencies"][i], 2)
                    })

            results.append(r_o)

    mongo_client.close( )

    populate_service_response( byc, results)
    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
