#!/usr/bin/env python3
import re, sys
from os import path, environ, pardir
from pymongo import MongoClient

from bycon import *

services_conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from bycon_bundler import *
from bycon_plot import *
from interval_utils import generate_genome_bins
from service_helpers import *
from service_response_generation import *

"""podmd
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167,pgx:icdom-85003
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgxcohort-TCGAcancers
* http://progenetix.test/services/intervalFrequencies/?datasetIds=progenetix&output=pgxmatrix&filters=NCIT:C7376,PMID:22824167
podmd"""

################################################################################
################################################################################
################################################################################

def main():
    try:
        interval_frequencies()
    except Exception:
        print_text_response(traceback.format_exc(), 302)

################################################################################

def intervalFrequencies():
    try:
        interval_frequencies()
    except Exception:
        print_text_response(traceback.format_exc(), 302)
   
################################################################################

def interval_frequencies():
    initialize_bycon_service()
    read_service_prefs("interval_frequencies", services_conf_path)
    generate_genome_bins()

    if (id_from_path := rest_path_value("intervalFrequencies")):
        BYC.update({"BYC_FILTERS": [ {"id": id_from_path } ] })
    elif "id" in BYC_PARS:
        BYC.update({"BYC_FILTERS": [ {"id": BYC_PARS["id"]} ] })
    pdb = ByconBundler().collationsPlotbundles()
    ifb = pdb.get("interval_frequencies_bundles", [])
    if len(BYC["ERRORS"]) >1:
        BeaconErrorResponse().response(422)

    file_type = BYC_PARS.get("output", "___none___")
    if "pgxseg" in file_type or "pgxfreq" in file_type:
        export_pgxseg_frequencies(ifb)
    elif "matrix" in file_type:
        export_pgxmatrix_frequencies(ifb)

    r = ByconautServiceResponse()
    print_json_response(r.populatedResponse(ifb))


################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
