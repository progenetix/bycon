from bycon_helpers import prdbug
from config import *

"""
This experimental authorization setup so far so far tests a method to define
the maximum response payload 

"""

################################################################################

def set_user_name(byc):
    """
    The default user is `anonymous`. If the environment is local the `local` user
    will be assumed - but can be overwritten later, e.g. for testing purposes.
    """
    # local user has full permissions
    if "local" in ENV:
        byc.update({"user_name": "local"})
        return
    un = BYC_PARS.get("user", "anonymous")
    if un in byc.get("authorizations", {}):
        byc.update({"user_name": un})


################################################################################

def set_returned_granularities(byc):
    rg = BYC_PARS.get("requested_granularity", "record")
    un = byc.get("user_name", "anonymous")
    auth = byc.get("authorizations", {})
    ds_ids = byc.get("dataset_ids", [])

    g_l_s = [0]
    r_g_l = GRANULARITY_LEVELS.get(rg, 0)

    if not "authorized_granularities" in byc:
        byc.update({"authorized_granularities": {}})
    for ds_id in byc["dataset_ids"]:
        byc["authorized_granularities"].update({ds_id: rg})
        ugs = auth.get(un, {})
        if ds_id in ugs:
            g_l_l = ugs[ds_id]
        elif "default" in ugs:
            g_l_l = ugs["default"]
        d_g_l = GRANULARITY_LEVELS.get(g_l_l, 0)
        if d_g_l <= r_g_l:
            byc["authorized_granularities"].update({ds_id: g_l_l})
        g_l_s.append(d_g_l)

    m_g_l = max(g_l_s)

    if m_g_l < r_g_l:
        prdbug("Warning: Requested granularity exceeds user authorization - using a maximum of %s" % byc["returned_granularity"])
        byc.update({"returned_granularity": list(GRANULARITY_LEVELS.keys())[m_g_l]})
    else:
        byc.update({"returned_granularity": list(GRANULARITY_LEVELS.keys())[r_g_l]})
