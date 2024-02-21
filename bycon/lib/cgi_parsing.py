import cgi, humps, json, re, sys
from urllib.parse import urlparse, parse_qs, unquote
from os import environ

from args_parsing import args_update_form
from bycon_helpers import prdbug, set_debug_state, test_truthy
from config import *

################################################################################

def parse_arguments(byc):
    a_defs = byc.get("argument_definitions", {})
    form = byc.get("form_data", {})
    for a, d in a_defs.items():
        if "default" in d:
            form.update({a: d["default"]})
    byc.update({"form_data": form})
    if "local" in ENV:
        args_update_form(byc)
    else:
        r_m = environ.get('REQUEST_METHOD', '')
        if "POST" in r_m:
            parse_POST(byc)
        else:
            parse_GET(byc)



################################################################################

def parse_POST(byc):
    content_len = environ.get('CONTENT_LENGTH', '0')
    content_typ = environ.get('CONTENT_TYPE', '')

    b_defs = byc.get("beacon_defaults", {})
    a_defs = byc.get("argument_definitions", {})
    form = byc.get("form_data", {})

    # TODO: catch error & return for non-json posts
    if "json" in content_typ:
        body = sys.stdin.read(int(content_len))
        jbod = json.loads(body)
        d_m = jbod.get("debugMode", False)
        BYC.update({"DEBUG_MODE": set_debug_state(d_m) })

        for j_p in jbod:
            j_p_d = humps.decamelize(j_p)
            if "debugMode" in j_p:
                continue
            # TODO: this hacks the v2 structure; ideally should use requestParameters schemas
            if "query" in j_p:
                for p, v in jbod["query"].items():
                    if p == "filters":
                        form.update({p: v})
                    elif p == "requestParameters":
                        for rp, rv in v.items():
                            rp_d = humps.decamelize(rp)
                            if "datasets" in rp:
                                if "datasetIds" in rv:
                                    form.update({"dataset_ids": rv["datasetIds"]})
                            elif "g_variant" in rp:
                                for vp, vv in v[rp].items():
                                    vp_d = humps.decamelize(vp)
                                    if vp_d in a_defs:
                                        form.update({vp_d: vv})
                            elif rp_d in a_defs:
                                form.update({rp_d: rv})
            else:
                if j_p_d in a_defs:
                    form.update({j_p_d: jbod.get(j_p)})

        # transferring pagination where existing to standard form values
        pagination = jbod.get("pagination", {})
        for p_k in ["skip", "limit"]:
            if p_k in pagination:
                if re.match(r'^\d+$', str(pagination[p_k])):
                    form.update({p_k: pagination[p_k]})
        byc.update({
            "form_data": form,
            "query_meta": jbod.get("meta", {})
        })


################################################################################

def parse_GET(byc):
    form = byc.get("form_data", {})
    a_defs = byc.get("argument_definitions", {})
    get_params = cgi.FieldStorage()
    for p in get_params:
        p_d = humps.decamelize(p)
        if p_d in a_defs:
            form.update({p_d: refactor_value_from_defined_type(p, get_params, a_defs[p_d])})
        else:
            prdbug(f'!!! Unmatched parameter {p_d}: {get_params.getvalue(p)}')
    byc.update({"form_data": form})
    BYC.update({"DEBUG_MODE": set_debug_state(byc["form_data"].get("debug_mode", False)) })


################################################################################

def rest_path_elements(byc):
    """
    The function deparses a Beacon REST path into its components and assigns
    those to the respective variables. The assumes structure is:

    `__root__/__request-entity__/__entity-id__/__response-entity__/?query...`
        |             |                 |               |
    "beacon"  e.g. "biosamples"  "pgxbs-t4ee3"  e.g. "genomicVariations"
        |             |                 |               |
    required      required          optional        optional
    """
    if not environ.get('REQUEST_URI'):
        return

    r_p_r = byc.get("request_path_root", "beacon")
    url_comps = urlparse(environ.get('REQUEST_URI'))
    url_p = url_comps.path
    p_items = re.split('/', url_p)

    if not r_p_r in p_items:
        return

    p_items = list(filter(None, p_items))
    r_i = p_items.index(r_p_r)

    if len(p_items) == r_i + 1:
        byc.update({"request_entity_path_id": "info"})
        return

    for p_k in ["request_entity_path_id", "request_entity_path_id_value", "response_entity_path_id"]:
        r_i += 1
        if r_i >= len(p_items):
            return
        p_v = unquote(p_items[r_i])
        byc.update({p_k: p_v})


################################################################################

def rest_path_value(key=""):
    """
    This function splits the path of the REQUEST_URI and returns the path element
    after a provided key. The typical uise case would be to get the entity or
    executing script, or an {id} value from a REST path e.g.

    * `/beacon/biosamples/?` => "beacon" -> "biosamples"
    * `/services/cytomapper/?` => "services" -> "cytomapper"
    * `/services/intervalFrequencies/NCIT:C3072/` => "intervalFrequencies" -> "NCIT:C3072"

    """

    if not environ.get('REQUEST_URI'):
        return None

    url_comps = urlparse(environ.get('REQUEST_URI'))
    p_items = re.split('/', url_comps.path)
    p_items = [x for x in p_items if len(x) > 1]
    p_items = [x for x in p_items if not "debug=" in x]

    for i, p in enumerate(p_items, 1):
        if len(p_items) > i:
            if unquote(p) in [key, f'{key}.py', unquote(key)]:
                return unquote(p_items[i])
        elif p == key:
            return None

    return None


################################################################################

def refactor_value_from_defined_type(parameter, form_data, definition):
    p_d_t = definition.get("type", "string")

    if "array" in p_d_t:
        values = form_return_listvalue(form_data, parameter)

        p_i_t = definition.get("items", "string")

        if "int" in p_i_t:
            return list(map(int, values))
        elif "number" in p_i_t:
            return list(map(float, values))
        else:
            return list(map(str, values))

    else:
        value = form_data.getvalue(parameter)
        prdbug(f'...refactor_value_from_defined_type: {parameter} {value}')

        if "int" in p_d_t:
            return int(value)
        elif "number" in p_d_t:
            return float(value)
        elif "bool" in p_d_t:
            return test_truthy(value)
        else:
            return str(value)


################################################################################

def form_return_listvalue(form_data, parameter):
    l_v = []
    if len(form_data) > 0:
        if parameter in form_data:
            v = form_data.getlist(parameter)
            if "null" in v:
                v.remove("null")
            if "undefined" in v:
                v.remove("undefined")
            if len(v) > 0:
                l_v = ','.join(v)
                l_v = l_v.split(',')

    return l_v


################################################################################

