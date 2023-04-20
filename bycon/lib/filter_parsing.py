import re

from cgi_parsing import *

################################################################################

def parse_filters(byc):

    get_global_filter_flags(byc)

    if not "filters" in byc["form_data"]:
        return byc

    fs = byc["form_data"]["filters"]
    fs = check_filter_values(fs, byc)
    if len(fs) > 0:
        byc.update( { "filters": fs } )
        return byc
            
    return byc

################################################################################

def get_global_filter_flags(byc):

    ff = {
        "logic": byc[ "config" ][ "filter_flags" ][ "logic" ],
        "precision": byc[ "config" ][ "filter_flags" ][ "precision" ],
        "descendants": byc[ "config" ][ "filter_flags" ][ "include_descendant_terms" ]
    }

    if "form_data" in byc:
        if "filter_logic" in byc[ "form_data" ]:
            ff["logic"] = boolean_to_mongo_logic( byc["form_data"]['filter_logic'] )
        if "filter_precision" in byc[ "form_data" ]:
            ff["precision"] = byc["form_data"]['filter_precision']
        if "include_descendant_terms" in byc[ "form_data" ]:
            i_d_t = str(byc[ "form_data" ].get("include_descendant_terms", 1)).lower()
            if i_d_t in ["0", "-1", "no", "false"]:
                ff["descendants"] = False

    byc.update( { "filter_flags": ff } )

    return byc

################################################################################

def check_filter_values(filters, byc):

    """
    The functtion checks the filter values for a match to any of the filter
    definitions. The optional `!` flag (no match) is not considered during
    evaluation ("deflagged").
    This filter check is complementary to the evaluation during the filter query
    generation and provides a warning if the filter pattern doesn't exist.
    """

    f_defs = byc["filter_definitions"]

    checked = [ ]
    for f in filters:
        if not isinstance(f, dict):
            f = {"id":f}
        if not "id" in f:
            continue

        if f not in checked:
            checked.append( f )

        deflagged = re.sub(r'^!', '', f["id"])
        matched = False
        for f_t, f_d in f_defs.items():
            if re.compile( f_d["pattern"] ).match( deflagged ):
                matched = True
                continue

        if matched is False:
            warning = "The filter `{}` does not match any defined filter pattern.".format(f["id"])
            response_add_filter_warnings(byc, warning)

    return checked

################################################################################

def response_add_filter_warnings(byc, message=False):

    if message is False:
        return byc
    if len(str(message)) < 1:
        return byc

    if not "service_response" in byc:
        return byc

    if not "info" in byc["service_response"]:
        byc["service_response"].update({"info": {}})
    if not "warnings" in byc["service_response"]:
        byc["service_response"]["info"].update({"warnings": []})

    byc["service_response"]["info"]["warnings"].append(message)

    return byc

