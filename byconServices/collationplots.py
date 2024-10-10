from bycon import BeaconErrorResponse, BYC, BYC_PARS, prdbug
from byconServiceLibs import ByconBundler, ByconPlot

"""podmd
* https://progenetix.org/services/collationplots/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167,pgx:icdom-85003
* https://progenetix.org/services/collationplots/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167&plotType=histoplot
* https://progenetix.org/services/collationplots/?datasetIds=progenetix&id=pgxcohort-TCGAcancers
* http://progenetix.test/services/collationplots/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167&plotType=histoheatplot
* http://progenetix.test/services/collationplots/?datasetIds=progenetix&collationTypes=NCIT&minNumber=500&plotType=histoheatplot&includeDescendantTerms=false
podmd"""

################################################################################

def collationplots():
    if str(BYC_PARS.get("plot_type", "___none___")) not in ["histoplot", "histoheatplot", "histosparkplot"]:
        BYC_PARS.update({"plot_type": "histoplot"})

    pdb = ByconBundler().collationsPlotbundles()
    BeaconErrorResponse().respond_if_errors()
    ByconPlot(pdb).svgResponse()
