#!/usr/bin/env python3

import cgi
import re, json, yaml
from os import path, environ, pardir
import sys, datetime, argparse
from pathlib import Path

from bycon import *

"""podmd

podmd"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        samples_plotter()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)

################################################################################

def samplesPlotter():
    
    try:
        samples_plotter()
    except Exception:
        print_text_response(traceback.format_exc(), byc["env"], 302)
   
################################################################################

def samples_plotter():

    initialize_bycon_service(byc)
    parse_variant_parameters(byc)
    generate_genomic_intervals(byc)


    byc["response_entity"].update({"response_schema": "beaconResultsetsResponse"})
    create_empty_beacon_response(byc)

    id_rest = rest_path_value("samplesPlotter")

    if not "empty_value" in id_rest:
        byc[ "file_id" ] = id_rest
    elif "file_id" in byc["form_data"]:
        byc[ "file_id" ] = byc["form_data"]["file_id"]

    if not "file_id" in byc:
        response_add_error(byc, 422, "No value was provided for collation `fileId`.")
    cgi_break_on_errors(byc)

    if not "plot" in byc.get("output", "handovers"):

        res_h_o = []
        h_o_types = byc["handover_definitions"]["h->o_types"]
        h_o_server = select_this_server(byc)

        for h_o_t in ["histoplot", "samplesplot"]:
            h_o_defs = h_o_types.get(h_o_t, {})
            h_o_defs.update({"script_path_web":"/services/samplesPlotter"})
            h_o_r = {
                "handover_type": {
                    "id": h_o_defs[ "id" ],
                    "label": f'{ h_o_defs.get("label", "generic handover") }'
                },
                "description": h_o_defs[ "description" ],
                "url": handover_create_url(h_o_server, h_o_defs, byc[ "file_id" ], byc),
                "pages": []
            }
            h_o_r.update({"url": re.sub("accessid", "fileId", h_o_r["url"])})
            res_h_o.append(h_o_r)

        r_set = {
            "exists": True,
            "resultsHandovers": res_h_o
        }

        byc["service_response"].update({
            "response_summary":{"exists":True},
            "response": {"result_sets": [r_set]}
        })

        cgi_print_response( byc, 200 )

    # TODO: maybe move to defaults file...
    if not "plot" in byc.get("output", "histoplot"):
        byc.update({"output": "histoplot"})

    inputfile = path.join( *config[ "server_tmp_dir_loc" ], byc[ "file_id" ] )

    if not path.exists(inputfile):
        response_add_error(byc, 422, f"The file path {inputfile} does not exist.")  
    cgi_break_on_errors(byc)

    bycon_bundle = pgxseg_return_bycon_bundle(inputfile, byc)
    cs_plot_data = bycon_bundle_create_callsets_plot_list(bycon_bundle, byc)
    interval_frequency_object = bycon_bundle_create_intervalfrequencies_object(bycon_bundle, byc)

    svg = samplesplot_svg_generator(byc, cs_plot_data)
    print_svg_response(svg, byc["env"])

    svg = histoplot_svg_generator(byc, [interval_frequency_object])
    print_svg_response(svg, byc["env"])

################################################################################
################################################################################

if __name__ == '__main__':
    main()
