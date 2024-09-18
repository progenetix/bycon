#!/usr/bin/env python3

from os import path, environ, pardir
import sys, datetime, argparse, traceback
from pymongo import MongoClient

from bycon import (
    BeaconErrorResponse,
    initialize_bycon_service,
    print_text_response,
    rest_path_value,
    BYC,
    BYC_PARS
)

services_lib_path = path.join( path.dirname( path.abspath(__file__) ), "lib" )
sys.path.append( services_lib_path )
from bycon_bundler import *
from bycon_plot import *
from file_utils import ExportFile
from interval_utils import generate_genome_bins
from service_helpers import *
from service_response_generation import *

"""podmd

* https://progenetix.org/services/collationplots/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167,pgx:icdom-85003
* https://progenetix.org/services/collationplots/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167&plotType=histoplot
* https://progenetix.org/services/collationplots/?datasetIds=progenetix&id=pgxcohort-TCGAcancers
* http://progenetix.test/services/collationplots/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167&plotType=histoheatplot
* http://progenetix.test/services/collationplots/?datasetIds=progenetix&collationTypes=NCIT&minNumber=500&plotType=histoheatplot&includeDescendantTerms=false
podmd"""

################################################################################
################################################################################
################################################################################

def main():
    try:
        collationplots()
    except Exception:
        print_text_response(traceback.format_exc(), 302)

################################################################################

def collationplots():
    initialize_bycon_service()
    generate_genome_bins()

    if (id_from_path := rest_path_value("collationplots")):
        BYC.update({"BYC_FILTERS": [ {"id": id_from_path } ] })
    elif "id" in BYC_PARS:
        BYC.update({"BYC_FILTERS": [ {"id": BYC_PARS["id"]} ] })
    if BYC_PARS.get("plot_type", "___none___") not in ["histoplot", "histoheatplot", "histosparkplot"]:
        BYC_PARS.update({"plot_type": "histoplot"})

    pdb = ByconBundler().collationsPlotbundles()
    if len(BYC["ERRORS"]) >1:
        BeaconErrorResponse().response(422)

    svg_f = ExportFile("svg").checkOutputFile()
    BP = ByconPlot(pdb)
    if svg_f:
        BP.svg2file(svg_f)
    else:
        BP.svgResponse()


################################################################################
################################################################################

if __name__ == '__main__':
    main()
