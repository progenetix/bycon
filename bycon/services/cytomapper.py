#!/usr/bin/env python3

import cgi, cgitb
import re, yaml
from os import path, pardir
import csv
import sys

pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
sys.path.append( pkg_path )
from bycon import *

################################################################################
################################################################################
################################################################################

def main():

    cytomapper()

################################################################################
################################################################################
################################################################################

def cytomapper():
    
    initialize_bycon_service(byc)
    
    parse_variant_parameters(byc)
    generate_genomic_intervals(byc)

    # response prototype
    create_empty_service_response(byc)

    cytoBands = [ ]
    if "cyto_bands" in byc["variant_pars"]:
        cytoBands, chro, start, end, error = bands_from_cytobands(byc["variant_pars"]["cyto_bands"], byc)
        byc["service_response"]["meta"]["received_request_summary"].update({ "cytoBands": byc["variant_pars"]["cyto_bands"] })
    elif "chro_bases" in byc["variant_pars"]:
        cytoBands, chro, start, end = bands_from_chrobases(byc["variant_pars"]["chro_bases"], byc)
        byc["service_response"]["meta"]["received_request_summary"].update({ "chroBases": byc["variant_pars"]["chro_bases"] })

    cb_label = cytobands_label( cytoBands )

    if len( cytoBands ) < 1:
        response_add_error(byc, 422, "No matching cytobands!" )
        cgi_break_on_errors(byc)

    size = int(  end - start )
    chroBases = "{}:{}-{}".format(chro, start, end)
    r_a = byc["variant_definitions"]["refseq_aliases"]
    sequence_id = r_a.get(chro, chro)

    if "text" in byc["output"]:
        open_text_streaming(byc["env"])
        print("{}\t{}".format(cb_label, chroBases))
        exit()

    # TODO: response objects from schema
    # r_s = byc["response_entity"]["beacon_schema"]["entity_type"]
    # cb_i = object_instance_from_schema_name(byc, r_s, "properties")
    
    results = [
        {
            "info": {
                "cytoBands": cb_label,
                "bandList": [x['chroband'] for x in cytoBands ],
                "chroBases": chroBases,
                "referenceName": chro,
                "size": size,
            },        
            "chromosome_location": {
                "type": "ChromosomeLocation",
                "species_id": "taxonomy:9606",
                "chr": chro,
                "interval": {
                    "start": cytoBands[0]["cytoband"],
                    "end": cytoBands[-1]["cytoband"],
                    "type": "CytobandInterval"
                }
            },
            "genomic_location": {
                "type": "SequenceLocation",
                "sequence_id": sequence_id,
                "interval": {
                    "start": {
                        "type": "Number",
                        "value": start
                    },
                    "end": {
                        "type": "Number",
                        "value": end
                    },
                    "type": "SequenceInterval"
                }
            }
        }
    ]

    populate_service_response( byc, results)
    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
