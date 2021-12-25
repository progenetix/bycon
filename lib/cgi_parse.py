import cgi, cgitb
from urllib.parse import urlparse, parse_qs, unquote
from os import environ
import json, sys
import re
import humps

################################################################################

def set_debug_state(debug=0):

    if debug > 0:
        cgitb.enable()
        print('Content-Type: text')
        print()
        return True

    elif environ.get('REQUEST_URI'):
        if "debug=1" in environ.get('REQUEST_URI'):
            cgitb.enable()
            print('Content-Type: text')
            print()
            return True

    return False

################################################################################

def cgi_parse_query(byc):

    content_len = environ.get('CONTENT_LENGTH', '0')
    content_typ = environ.get('CONTENT_TYPE', '')
    r_m = environ.get('REQUEST_METHOD', '')

    form_data = {}
    query_meta = {}
    debug_state = False

    # set_debug_state(1)

    if r_m == "POST":
        body = sys.stdin.read(int(content_len))

        if "json" in content_typ:
            jbod = json.loads(body)
            if "debug" in jbod:
                if jbod["debug"] > 0:                 
                    debug_state = set_debug_state(1)

            # TODO: this hacks the v2b4 structure
            if "query" in jbod:
                for p, v in jbod["query"].items():
                    if p == "requestParameters":
                        for rp, rv in v.items():
                            form_data[rp] = rv
                    else:
                        form_data[p] = v

            # TODO: define somewhere else with proper defaults
            form_data["requested_granularity"] = jbod.get("requestedGranularity", "record")
            form_data["include_resultset_responses"] = jbod.get("includeResultsetResponses", "HIT")

            if "pagination" in jbod:
                for sp in ["skip", "limit"]:
                    form_data[sp] = jbod["pagination"].get(sp, 0)

            form_data["filters"] = jbod.get("filters", [] )
            query_meta = jbod.get("meta", {})

        return form_data, query_meta, debug_state

    debug_state = set_debug_state()

    # TODO: The structure, types of the request/form object need to go to a
    # config and some deeper processing, for proper beacon request objects
    # also, defaults etc.
    get = cgi.FieldStorage()
    form_data = {}

    for p in get:
        if p in byc["config"]["list_pars"]:
            form_data.update({p: form_return_listvalue( get, p )})
        else:
            form_data.update({p: get.getvalue(p)})

    #TODO: re-evaluate hack of empty filters which avoids dirty errors downstream
    if not "filters" in form_data:
        form_data.update({"filters": []})

    form_data.update({"requested_granularity": get.getvalue("requestedGranularity", "record")})
    form_data.update({"include_resultset_responses": get.getvalue("includeResultsetResponses", "HIT")})
    
    return form_data, query_meta, debug_state

################################################################################

def rest_path_value(key=""):

    r_p_v = "empty_value"

    if not environ.get('REQUEST_URI'):
        return r_p_v

    url_comps = urlparse( environ.get('REQUEST_URI') )
    url_p = url_comps.path
    p_items = re.split('/', url_p)

    if "debug=1" in p_items:
        p_items.remove("debug=1")

    i = 0
    f = ""

    if len(p_items[-1]) < 2:
        del p_items[-1]

    for p in p_items:

        i += 1
        if len(p_items) > i:
            if unquote(p) in [key, key+".py", unquote(key)]:
                return unquote(p_items[ i ])
        elif p == key:
            return r_p_v

    return r_p_v

################################################################################

def form_return_listvalue( form_data, parameter ):

    l_v = [ ]
    if len(form_data) > 0:
        if parameter in form_data:
            v = form_data.getlist( parameter )
            if "null" in v:
                v.remove("null")
            if "undefined" in v:
                v.remove("undefined")
            if len(v) > 0:
                l_v  = ','.join(v)
                l_v  = l_v.split(',')

    return l_v 

################################################################################

def cgi_print_rewrite_response(uri_base="", uri_stuff="", output_par="empty_value"):

    print("Status: 302")
    print("Location: {}{}".format(uri_base, uri_stuff))
    print()
    exit()

################################################################################

def cgi_print_text_response(byc, status_code):

    print('Content-Type: text')
    print('status:'+str(status_code))
    print()
    print(byc["service_response"]+"\n")
    exit()

################################################################################

def cgi_simplify_response(byc):

    r = byc["service_response"]

    if "result_sets" in r:
        if "results" in r["result_sets"][0]:
            byc.update({ "service_response": r["result_sets"][0]["results"] })
    elif "response" in r:
        if "results" in r["response"]:
            byc.update({ "service_response": r["response"]["results"] })

    return byc

################################################################################

def cgi_break_on_errors(byc):

    r = byc["service_response"]
    e = byc["error_response"]

    # TODO: temp hack
    for k in byc["service_response"].keys():
        if "any_of" in byc["service_response"][k]:
            byc["service_response"][k].pop("any_of")
        if "all_of" in byc["service_response"][k]:
            byc["service_response"][k].pop("all_of")

    if e["error"]["error_code"] > 200:
        cgi_print_response( byc, e["error"]["error_code"] )

################################################################################

def cgi_debug_message(byc, label, debug_object):

    try:
        if byc["debug_state"]:
            print("{}:\n\n{}\n\n".format(label, debug_object))
    except:
        pass

################################################################################

def cgi_print_response(byc, status_code):

    r_f = ""
    f_d = {}

    if "form_data" in byc:
        f_d = byc["form_data"]

    if "responseFormat" in f_d:
        r_f = f_d["responseFormat"]

    # This is a simple "de-jsonify", intended to be used for already
    # pre-formatted list-like items (i.e. lists only containing objects)
    # with simple key-value pairs)
    # TODO: universal text table converter
    if "output" in byc:
        if "text" in byc["output"]:

            cgi_simplify_response(byc)

            if isinstance(byc["service_response"], dict):
                byc.update({ "service_response": json.dumps(humps.camelize(byc["service_response"]), default=str) })
            if isinstance(byc["service_response"], list):
                l_d = [ ]
                for dp in byc["service_response"]:
                    v_l = [ ]
                    for v in dp.values():
                        v_l.append(str(v))
                    l_d.append("\t".join(v_l))
                byc.update({ "service_response": "\n".join(l_d) })
            cgi_print_text_response(byc, status_code)

    if "simple" in r_f:
        cgi_simplify_response(byc)

    response_clean_legacy(byc)
    update_error_code_from_response_summary(byc)
    switch_to_error_response(byc)

    print('Content-Type: application/json')
    print('status:200')
    print()
    prjsoncam(byc["service_response"])
    exit()

################################################################################

def response_clean_legacy(byc):

    legacy = ["result_sets", "data"]

    for k in legacy:
        byc["service_response"].pop(k, None)

    return byc

################################################################################

def update_error_code_from_response_summary(byc):

    if not "response_summary" in byc["service_response"]:
        return byc

    if not "exists" in byc["service_response"]["response_summary"]:
        return byc

################################################################################

def switch_to_error_response(byc):

    if byc["error_response"]["error"]["error_code"] > 200:
        if "meta" in byc["service_response"]:
            byc["error_response"].update({ "meta": byc["service_response"]["meta"]})
        byc["service_response"] = byc["error_response"]

    return byc

################################################################################

def check_switch_to_boolean_response(byc):

    try:
        if byc["service_response"]["meta"]["received_request_summary"]["requested_granularity"] == "boolean":
            byc["service_response"].pop("response", None)
            byc["service_response"]["response_summary"].pop("num_total_results", None)
            byc["service_response"]["meta"].update({"returned_granularity": "boolean"})
    except:
        pass

    return byc

################################################################################

def check_switch_to_count_response(byc):

    try:
        if byc["service_response"]["meta"]["received_request_summary"]["requested_granularity"] == "count":
            byc["service_response"].pop("response", None)
            byc["service_response"]["meta"].update({"returned_granularity": "count"})
    except:
        pass

    return byc

################################################################################
################################################################################
################################################################################

def open_json_streaming(byc, filename="data.json"):

    print('Content-Type: application/json')
    print('Content-Disposition: attachment; filename="{}"'.format(filename))
    print('status: 200')
    print()
    print('{"meta":', end = '')
    print(json.dumps(humps.camelize(byc["service_response"]["meta"]), indent=None, sort_keys=True, default=str), end=",")
    print('"response":{', end='')
    for r_k, r_v in byc["service_response"].items():
        if "results" in r_k:
            continue
        print('"'+r_k+'":', end='')
        print(json.dumps(humps.camelize(r_v), indent=None, sort_keys=True, default=str), end=",")
    print('"results":[', end="")

################################################################################

def close_json_streaming():
    print(']}}')
    exit()

################################################################################

def open_text_streaming(filename="data.pgxseg"):

    print('Content-Type: text/pgxseg')
    print('Content-Disposition: attachment; filename="{}"'.format(filename))
    print('status: 200')
    print()

################################################################################

def close_text_streaming():

    print()
    exit()

################################################################################

def prjsoncam(this):
    print(json.dumps(humps.camelize(this), indent=4, sort_keys=True, default=str)+"\n")

################################################################################

def prjsonresp(this={}):

    print('Content-Type: application/json')
    print('status:200')
    print()
    prjsoncam(this)
    exit()



