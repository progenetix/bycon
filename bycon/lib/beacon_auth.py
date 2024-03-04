from bycon_helpers import prdbug
from config import *

"""
This experimental authorization setup so far so far tests a method to define
the maximum response payload 

"""

################################################################################

def set_user_name(byc):
    """
    The default user is `anonymous`. Their access granularity is defined in 
    `config.py` => `AUTH_DEFAULTS`.
    If the environment is local the `local` user will be assumed - but can be
    overwritten later, e.g. for testing purposes.
    """
    # local user has full permissions
    if "local" in ENV:
        BYC.update({"USER": "local"})
    elif (un := BYC_PARS.get("user_name", "anonymous")) in byc.get("authorizations", {}):
        BYC.update({"USER": un})

################################################################################

def set_returned_granularities(byc):
    """
    This method sets the returned granularity **per dataset** based on the user's
    authorizations.
    CAVE: So far this is only used for "data" responses (variants, biosamples...)
    **not** for "info"-type responses anf `filtering_terms`.
    """
    auth = byc.get("authorizations", {})
    ds_ids = byc.get("dataset_ids", [])

    for ak, av in auth.items():
        AUTHORIZATIONS.update({ak: av})

    # found allowed granularity levels
    g_l_s = [0]
    # requested granularity level
    rg = BYC_PARS.get("requested_granularity", "record")
    r_g_l = GRANULARITY_LEVELS.get(rg, 0)

    if not "authorized_granularities" in byc:
        byc.update({"authorized_granularities": {}})

    for ds_id in ds_ids:
        byc["authorized_granularities"].update({ds_id: rg})
        
        # the user is checked against predefined authorizations
        if not (ugs := AUTHORIZATIONS.get(BYC["USER"])):
            continue

        g_l_l = ugs.get("default", "___none___")
        if ds_id in ugs:
            g_l_l = ugs[ds_id]

        d_g_l = GRANULARITY_LEVELS.get(g_l_l, 0)
        if d_g_l <= r_g_l:
            byc["authorized_granularities"].update({ds_id: g_l_l})
        g_l_s.append(d_g_l)
    m_g_l = max(g_l_s)

    if m_g_l < r_g_l:
        prdbug(f'Warning: Requested granularity exceeds user authorization - using a maximum of {m_g_l}')
        byc.update({"returned_granularity": list(GRANULARITY_LEVELS.keys())[m_g_l]})
    else:
        byc.update({"returned_granularity": list(GRANULARITY_LEVELS.keys())[r_g_l]})
