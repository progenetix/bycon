from bycon import BYC_PARS, BeaconErrorResponse
from byconServiceLibs import ByconBundler, GenomeBins, ByconServiceResponse, PGXfreq

"""
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,pubmed:22824167,pgx:icdom-85003
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgx:cohort-TCGAcancers
* http://progenetix.test/services/intervalFrequencies/?datasetIds=progenetix&output=pgxmatrix&filters=NCIT:C7376,pubmed:22824167
"""

def intervalFrequencies():
    pdb = ByconBundler().collationsPlotbundles()
    ifb = pdb.get("interval_frequencies_bundles", [])

    BeaconErrorResponse().respond_if_errors()

    file_type = BYC_PARS.get("output", "___none___")
    if "pgxseg" in file_type or "pgxfreq" in file_type:
        PGXfreq(ifb).stream_pgxfreq()
    elif "matrix" in file_type:
        PGXfreq(ifb).stream_pgxmatrix()

    ByconServiceResponse().print_populated_response(ifb)
