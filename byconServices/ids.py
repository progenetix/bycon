import re
from os import path

from bycon import (
    BeaconErrorResponse,
    BYC,
    BYC_PARS,
    prdbug,
    print_uri_rewrite_response,
    ByconParameters
)
from byconServiceLibs import read_service_prefs

################################################################################

def ids():
    """
    The `ids` service forwards compatible, prefixed ids (see `config/ids.yaml`) to specific
    website endpoints. There is no check if the id exists; this is left to the web
    page handling itself.

    Stacking with the "pgx:" prefix is allowed.

    #### Examples (using the Progenetix resource as endpoint):

    * <https://progenetix.org/services/ids/pgxbs-kftva5zv>
    * <https://progenetix.org/services/ids/pubmed:28966033>
    * <https://progenetix.org/services/ids/NCIT:C3262>
    """

    conf_path = path.join( path.dirname( path.abspath(__file__) ), "config" )
    read_service_prefs( "ids", conf_path)
    s_c = BYC.get("service_config", {})
    f_p_s = s_c.get("format_patterns", {})

    if len(lid := BYC_PARS.get("id", "")) > 0:
        for f_p in f_p_s:
            pat = re.compile(f_p["pattern"])
            if pat.match(lid):
                link = f_p.get("link", "http://localhost")
                if len(pim := f_p.get("prepend_if_missing", "")) > 0:
                    if pim in lid:
                        pass
                    else:
                        lid = pim+lid
                print_uri_rewrite_response(f'{link}{lid}')

    BYC.update({"ERRORS": ["No correct id provided. Please refer to the documentation at http://info.progenetix.org/"]})
    BeaconErrorResponse().respond_if_errors()
