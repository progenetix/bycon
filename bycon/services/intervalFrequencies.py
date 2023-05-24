#!/usr/bin/env python3

import cgi
import re, json, yaml
from os import path, environ, pardir
import sys, datetime, argparse
from pymongo import MongoClient

from bycon import *

"""podmd

* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgxcohort-TCGAcancers
* https://progenetix.org/cgi/bycon/services/intervalFrequencies.py/?output=pgxseg&datasetIds=progenetix&filters=NCIT:C7376

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        interval_frequencies()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)

################################################################################

def intervalFrequencies():
    
    try:
        interval_frequencies()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)
   
################################################################################

def interval_frequencies():

    initialize_bycon_service(byc)

    select_dataset_ids(byc)
    parse_filters(byc)
    parse_variant_parameters(byc)
    generate_genomic_intervals(byc)
    create_empty_service_response(byc)
    cgi_break_on_errors(byc)

    id_rest = rest_path_value("intervalFrequencies")

    if id_rest is not None:
        byc[ "filters" ] = [ {"id": id_rest } ]
    elif "id" in byc["form_data"]:
        byc[ "filters" ] = [ {"id": byc["form_data"]["id"]} ]

    if not "filters" in byc:
        response_add_error(byc, 422, "No value was provided for collation `id` or `filters`.")  
    cgi_break_on_errors(byc)

    # data retrieval & response population
    f_coll_name = byc["config"]["frequencymaps_coll"]
    c_coll_name = byc["config"]["collations_coll"]

    fmap_name = "frequencymap"
    if "codematches" in byc["method"]:
        fmap_name = "frequencymap_codematches"

    results = [ ]

    mongo_client = MongoClient( )
    for ds_id in byc[ "dataset_ids" ]:

        for f in byc[ "filters" ]:

            f_val = f["id"]
 
            collation_f = mongo_client[ ds_id ][ f_coll_name ].find_one( { "id": f_val } )
            collation_c = mongo_client[ ds_id ][ c_coll_name ].find_one( { "id": f_val } )

            if collation_f is None:
                continue

            if "with_samples" in byc["form_data"]: 
                if int(byc["form_data"]["with_samples"]) > 0:
                    if int(collation_c[ "code_matches" ]) < 1:
                        continue

            if not fmap_name in collation_f:
                continue

            if not collation_f:
                response_add_error(byc, 422, "No collation {} was found in {}.{}".format(f_val, ds_id, f_coll_name))
            if not collation_c:
                response_add_error(byc, 422, "No collation {} was found in {}.{}".format(f_val, ds_id, c_coll_name))
            cgi_break_on_errors(byc)

            s_c = collation_c["count"]
            if "analysis_count" in collation_f[ fmap_name ]:
               s_c = collation_f[ fmap_name ]["analysis_count"]

            i_d = collation_c["id"]
            r_o = {
                "dataset_id": ds_id,
                "group_id": i_d,
                "label": re.sub(r';', ',', collation_c["label"]),
                "sample_count": s_c,
                "interval_frequencies": collation_f[ fmap_name ]["intervals"] }
                
            results.append(r_o)

    mongo_client.close( )

    plot_data_bundle = { "interval_frequencies_bundles": results }
    ByconPlot(byc, plot_data_bundle).svg_response()

    check_pgxseg_frequencies_export(byc, results)
    check_pgxmatrix_frequencies_export(byc, results)
    populate_service_response( byc, results)
    cgi_print_response( byc, 200 )

################################################################################

def check_pgxseg_frequencies_export(byc, results):

    if not "pgxseg" in byc["output"] and not "pgxfreq" in byc["output"]:
        return

    export_pgxseg_frequencies(byc, results)

################################################################################

def check_pgxmatrix_frequencies_export(byc, results):

    if not "pgxmatrix" in byc["output"]:
        return

    export_pgxmatrix_frequencies(byc, results)

################################################################################
################################################################################

if __name__ == '__main__':
    main()
