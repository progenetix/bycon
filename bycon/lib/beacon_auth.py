from cgi_parsing import prdbug

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
    if "local" in byc["env"]:
        byc.update({"user_name": "local"})
        return

    form = byc.get("form_data", {})
    un = form.get("user", "anonymous")
    if un in byc.get("authorizations", {}):
        byc.update({"user_name": un})


################################################################################

def set_returned_granularities(byc):

    form = byc.get("form_data", {})
    rg = form.get("requested_granularity", "record")
    un = byc.get("user_name", "anonymous")
    granularity_levels = byc.get("granularity_levels", {})
    auth = byc.get("authorizations", {})
    ds_ids = byc.get("dataset_ids", [])

    g_l_s = [0]
    r_g_l = granularity_levels.get(rg, 0)

    if not "authorized_granularities" in byc:
        byc.update({"authorized_granularities": {}})

    for ds_id in byc["dataset_ids"]:
        byc["authorized_granularities"].update({ds_id: rg})
        ugs = auth.get(un, {})
        if ds_id in ugs:
            g_l_l = ugs[ds_id]
        elif "default" in ugs:
            g_l_l = ugs["default"]
        d_g_l = granularity_levels.get(g_l_l, 0)
        if d_g_l <= r_g_l:
            byc["authorized_granularities"].update({ds_id: g_l_l})
        g_l_s.append(d_g_l)

    m_g_l = max(g_l_s)

    if m_g_l < r_g_l:
        prdbug("Warning: Requested granularity exceeds user authorization - using a maximum of %s" % byc["returned_granularity"], byc.get("debug_mode"))
        byc.update({"returned_granularity": list(granularity_levels.keys())[m_g_l]})
    else:
        byc.update({"returned_granularity": list(granularity_levels.keys())[r_g_l]})
