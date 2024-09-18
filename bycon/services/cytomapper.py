#!/usr/bin/env python3
import sys, traceback
from os import path

from bycon import *

services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from cytoband_utils import *
from service_helpers import *
from service_response_generation import *

"""
cytomapper.py --cytoBands 8q21 
cytomapper.py --chroBases 4:12000000-145000000

"""

################################################################################
################################################################################
################################################################################

def main():

    try:
        cytomapper()
    except Exception:
        print_text_response(traceback.format_exc(), 302)

################################################################################
################################################################################
################################################################################

def cytomapper():
    
    initialize_bycon_service()
    results = __return_cytobands_results()

    r = ByconautServiceResponse()
    response = r.populatedResponse(results)

    if len( results ) < 1:
        BYC["ERRORS"].append("No matching cytobands!")
        BeaconErrorResponse().response(422)

    if "cyto_bands" in BYC_PARS:
        response["meta"]["received_request_summary"].update({ "cytoBands": BYC_PARS["cyto_bands"] })
    elif "chro_bases" in BYC_PARS:
        response["meta"]["received_request_summary"].update({ "chroBases": BYC_PARS["chro_bases"] })

    print_json_response(response)


################################################################################

def __return_cytobands_results():

    chro_names = ChroNames()

    results = []
    if "cyto_bands" in BYC_PARS:
        parlist = BYC_PARS["cyto_bands"]
    elif "chro_bases" in BYC_PARS:
        parlist = BYC_PARS["chro_bases"]

    if "text" in BYC_PARS.get("output", "___none___"):
        open_text_streaming()

    for p in parlist:
        cytoBands = [ ]
        if "cyto_bands" in BYC_PARS:
            cytoBands, chro, start, end, error = bands_from_cytobands(p)
        elif "chro_bases" in BYC_PARS:
            cytoBands, chro, start, end = bands_from_chrobases(p)

        if len( cytoBands ) < 1:
            continue

        cb_label = cytobands_label( cytoBands )
        size = int(  end - start )
        chroBases = "{}:{}-{}".format(chro, start, end)
        sequence_id = chro_names.refseq(chro)

        if "text" in BYC_PARS.get("output", "___none___"):
            print(f'{chro}{cb_label}\t{chroBases}')

        # TODO: response objects from schema
        results.append(
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
        )

    if "text" in BYC_PARS.get("output", "___none___"):
        exit()

    return results


################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
