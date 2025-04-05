#!/usr/local/bin/python3

from bycon import BeaconErrorResponse, BYC, BYC_PARS, prdbug
from byconServiceLibs import ByconBundler, ByconPlot

################################################################################

def collationplots():
    """
    The `collationplots` function is a service to provide plots for CNV data aggregated
    for samples matching individual filter values such as diagnostic codes or experimental
    series id values. The default response is an SVG histogram ("histoplot"). Please refer
    to the plot parameters documentation and the `ByconPlot` class for other options.

    For a single plot one can provide the entity id as path id value.
    
    #### Examples (using the Progenetix resource as endpoint):

    * https://progenetix.org/services/collationplots/pgx:cohort-TCGAcancers
    * https://progenetix.org/services/collationplots/?filters=NCIT:C7376,pubmed:22824167,pgx:icdom-85003
    * https://progenetix.org/services/collationplots/?filters=NCIT:C7376,pubmed:22824167&plotType=histoheatplot
    * https://progenetix.org/services/collationplots/?collationTypes=icdom&minNumber=1000&plotType=histoheatplot
    """
    pdb = ByconBundler().collationsPlotbundles()
    BeaconErrorResponse().respond_if_errors()
    ByconPlot(pdb).svgResponse()
