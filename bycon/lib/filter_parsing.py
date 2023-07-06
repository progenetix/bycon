import re

from cgi_parsing import boolean_to_mongo_logic

################################################################################

def parse_filters(byc):

    get_global_filter_flags(byc)
    byc.update( { "filters": check_filter_values(byc) } )


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

################################################################################

def check_filter_values(byc):

    """
    The function checks the filter values for a match to any of the filter
    definitions. The optional `!` flag (no match) is not considered during
    evaluation ("deflagged").
    This filter check is complementary to the evaluation during the filter query
    generation and provides a warning if the filter pattern doesn't exist.
    """

    checked = [ ]
    filters = byc["form_data"].get("filters")
    if not filters:
        return checked

    f_defs = byc["filter_definitions"]

    for f in filters:
        if not isinstance(f, dict):
            f = {"id":f}
        if not "id" in f:
            continue

        deflagged = re.sub(r'^!', '', f["id"])
        matched = False
        for f_t, f_d in f_defs.items():
            if re.compile( f_d["pattern"] ).match( deflagged ):
                # print(f'{f_d["pattern"]} => ? {deflagged}')
                matched = True
                continue

        if matched is False:
            warning = "The filter `{}` does not match any defined filter pattern.".format(f["id"])
            response_add_filter_warnings(byc, warning)

        if f not in checked:
            checked.append( f )

    return checked


################################################################################

def response_add_filter_warnings(byc, message=False):

    if message is False:
        return

    if len(str(message)) < 1:
        return

    if not "service_response" in byc:
        return

    if not "info" in byc["service_response"] or byc["service_response"]["info"] is None:
        byc["service_response"].update({"info": {"warnings":[]}})
    if not "warnings" in byc["service_response"]["info"] or byc["service_response"]["info"]["warnings"] is None:
        byc["service_response"]["info"].update({"warnings": []})

    byc["service_response"]["info"]["warnings"].append(message)
