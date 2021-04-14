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

"""podmd

* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgxcohort-TCGAcancers
* https://progenetix.org/cgi/bycon/services/intervalFrequencies.py/?method=pgxseg&datasetIds=progenetix&filters=NCIT:C7376

podmd"""

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
            r_o = {
                "dataset_id": ds_id,
                "collation_id": i_d,
                "label": re.sub(r';', ',', subset["label"]),
                # "sample_count": subset["count"],
                "interval_frequencies": [ ] }
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

    _export_pgxseg_frequencies(byc, results)
    populate_service_response( byc, results)
    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################

def _export_pgxseg_frequencies(byc, results):

    if not "pgxseg" in byc["method"]:
        return

    open_text_streaming("interval_frequencies.pgxseg")

    h_ks = ["chro", "start", "end", "gain_frequency", "loss_frequency", "index"]

    for f_set in results:
        m_line = []
        for k in ["collation_id", "label", "dataset_id"]: #, "sample_count"
            m_line.append(k+"="+str(f_set[k]))
        print("#"+';'.join(m_line))

    print("collation_id\t"+"\t".join(h_ks))

    for f_set in results:
        for intv in f_set["interval_frequencies"]:
            v_line = [ ]
            v_line.append(f_set[ "collation_id" ])
            for k in h_ks:
                v_line.append(str(intv[k]))
            print("\t".join(v_line))

    close_text_streaming()

################################################################################
################################################################################


if __name__ == '__main__':
    main()
