import re

from bycon_helpers import prdbug, test_truthy
from config import *

################################################################################

def parse_filters(byc):
    """
    The function checks the filter values for a match to any of the filter
    definitions. The optional `!` flag (no match) is not considered during
    evaluation ("deflagged").
    This filter check is complementary to the evaluation during the filter query
    generation and provides a warning if the filter pattern doesn't exist.
    """
    f_defs = byc["filter_definitions"]
    filters = BYC_PARS.get("filters", [])
    checked = [ ]
    for f in filters:
        if not isinstance(f, dict):
            f = {"id":f}
        if not "id" in f:
            continue
        deflagged = re.sub(r'^!', '', f["id"])
        matched = False
        for f_t, f_d in f_defs.items():
            if re.compile( f_d["pattern"] ).match( deflagged ):
                matched = True
                continue
        if matched is False:
            BYC["WARNINGS"].append( f'The filter {f["id"]} does not match any defined filter pattern.')

        if f not in checked:
            checked.append( f )
    byc.update({"filters": checked})

