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
from beaconServer.lib.cytoband_utils import *
from beaconServer.lib.interval_utils import *

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

    cgi_break_on_errors(byc)

    id_rest = rest_path_value("intervalFrequencies")

    if not "empty_value" in id_rest:
        byc[ "filters" ] = [ id_rest ]
    elif "id" in byc["form_data"]:
        byc[ "filters" ] = [ byc["form_data"].getvalue( "id" ) ]

    if not "filters" in byc:
        response_add_error(byc, 422, "No value was provided for collation `id` or `filters`.")  
    cgi_break_on_errors(byc)

    # data retrieval & response population
    f_coll_name = byc["these_prefs"]["frequency_collection_name"]
    c_coll_name = "collations"

    results = [ ]

    mongo_client = MongoClient( )
    for ds_id in byc[ "dataset_ids" ]:
        for f in byc[ "filters" ]:
 
            collation_f = mongo_client[ ds_id ][ f_coll_name ].find_one( { "id": f } )
            collation_c = mongo_client[ ds_id ][ c_coll_name ].find_one( { "id": f } )

            if not collation_f:
                response_add_error(byc, 422, "No collation {} was found in {}.{}".format(f, ds_id, f_coll_name))
            if not collation_c:
                response_add_error(byc, 422, "No collation {} was found in {}.{}".format(f, ds_id, c_coll_name))
            cgi_break_on_errors(byc)

            i_d = collation_c["id"]
            r_o = {
                "dataset_id": ds_id,
                "group_id": i_d,
                "label": re.sub(r';', ',', collation_c["label"]),
                "sample_count": collation_c["count"],
                "interval_frequencies": [ ] }
            for interval in byc["genomic_intervals"]:
                i = interval["index"]
                # TODO: Error if length ...
                r_o["interval_frequencies"].append( {
                    "index": i,
                    "chro": interval["chro"],
                    "start": interval["start"],
                    "end": interval["end"],
                    "gain_frequency": round(collation_f["frequencymaps"]["dupfrequencies"][i], 2),
                    "loss_frequency": round(collation_f["frequencymaps"]["delfrequencies"][i], 2)
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

    print("#meta=>genome_binning={};interval_number={}".format(byc["genome_binning"], len(byc["genomic_intervals"])) )
    h_ks = ["chro", "start", "end", "gain_frequency", "loss_frequency", "index"]

    # should get error checking if made callable

    for f_set in results:
        m_line = []
        for k in ["group_id", "label", "dataset_id", "sample_count"]:
            m_line.append(k+"="+str(f_set[k]))
        print("#group=>"+';'.join(m_line))

    print("group_id\t"+"\t".join(h_ks))

    for f_set in results:
        for intv in f_set["interval_frequencies"]:
            v_line = [ ]
            v_line.append(f_set[ "group_id" ])
            for k in h_ks:
                v_line.append(str(intv[k]))
            print("\t".join(v_line))

    close_text_streaming()

################################################################################
################################################################################


if __name__ == '__main__':
    main()
