from bycon import BYC_PARS, BeaconErrorResponse, BeaconDataResponse, GenomeBins, print_json_response
from byconplus import ByconBundler, PGXfreq
from lib.service_response_generation import ByconServiceResponse

"""
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,pubmed:22824167,pgx:icdom-85003
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgx:cohort-TCGAcancers
* http://progenetix.test/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,pubmed:22824167
"""

def intervalFrequencies():
    pdb = ByconBundler().collationsPlotbundles()
    ifb = pdb.get("interval_frequencies_bundles", [])

    BeaconErrorResponse().respond_if_errors()

    file_type = BYC_PARS.get("output", "___none___")
    if "pgxseg" in file_type or "pgxfreq" in file_type:
        PGXfreq(ifb).streamPGXfreq()
    elif "matrix" in file_type:
        PGXfreq(ifb).streamPGXmatrix()

    ByconServiceResponse().print_populated_response(ifb)
