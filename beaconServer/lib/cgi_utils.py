import cgi, cgitb
from urllib.parse import urlparse, parse_qs
from os import environ
import json, sys
import re
from humps import camelize

################################################################################

def set_debug_state(debug=0):

    if debug > 0:
        cgitb.enable()
        print('Content-Type: text')
        print()
    elif environ.get('REQUEST_URI'):
        if "debug=1" in environ.get('REQUEST_URI'):
            cgitb.enable()
            print('Content-Type: text')
            print()

################################################################################

def cgi_parse_query(byc):

    content_len = environ.get('CONTENT_LENGTH', '0')
    content_typ = environ.get('CONTENT_TYPE', '')
    method = environ.get('REQUEST_METHOD', '')

    form_data = {}
    query_meta = {}

    # set_debug_state(1)

    if "POST" in method:
        body = sys.stdin.read(int(content_len))
        if "json" in content_typ:
            jbod = json.loads(body)
            # print(jbod)
            if "debug" in jbod:
                if jbod["debug"] > 0:                 
                    set_debug_state(1)
            # TODO: this hacks the v2b4 structure
            if "query" in jbod:
                for p, v in jbod["query"].items():
                    if p == "requestParameters":
                        for rp, rv in v.items():
                            form_data[rp] = rv
                    else:
                        form_data[p] = v
            if "filters" in jbod:
                form_data["filters"] = jbod["filters"]
            if "meta" in jbod:
                query_meta = jbod["meta"]

        return form_data, query_meta

    set_debug_state()

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
    
    return form_data, query_meta

################################################################################

def rest_path_value(key=""):

    r_p_v = "empty_value"

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
            if p in [key, key+".py"]:
                return p_items[ i ]
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

def cgi_print_rewrite_response(uri_base="", uri_stuff=""):

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

    if "data" in r:            
        byc.update({ "service_response": r["data"] })
        # TODO
    elif "result_sets" in r:
        if "results" in r["result_sets"][0]:
            byc.update({ "service_response": r["result_sets"][0]["results"] })
    elif "results" in r:
        byc.update({ "service_response": r["results"] })

    return byc

################################################################################

def cgi_break_on_errors(byc):

    r = byc["service_response"]
    
    if "response" in r and "form_data" in byc:
        if "error" in r:
            if r["error"]["error_code"] > 200:
                cgi_print_response( byc, r["error"]["error_code"] )

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
    if "text" in byc["output"]:
        cgi_simplify_response(byc)

        if isinstance(byc["service_response"], dict):
            byc.update({ "service_response": json.dumps(camelize(byc["service_response"]), default=str) })
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

    if "response" in byc["service_response"]:
        if "error" in byc["service_response"]:
            byc["service_response"]["error"].update({"error_code": status_code })

    if "response_summary" in byc["service_response"]:
        if "exists" in byc["service_response"]["response_summary"]:
            if byc["service_response"]["response_summary"]["exists"] is False:
                status_code = 422
#    print(byc["service_response"]["result_sets"])

    print('Content-Type: application/json')
    print('status:'+str(status_code))
    print()
    print(json.dumps(camelize(byc["service_response"]), indent=4, sort_keys=True, default=str)+"\n")
    exit()

################################################################################
################################################################################
################################################################################

def open_json_streaming(byc, filename="data.json"):

    print('Content-Type: application/json')
    print('Content-Disposition: attachment; filename="{}"'.format(filename))
    print('status: 200')
    print()
    print('{"meta":', end = '')
    print(json.dumps(camelize(byc["service_response"]["meta"]), indent=None, sort_keys=True, default=str), end=",")
    print('"response":{', end='')
    for r_k, r_v in byc["service_response"].items():
        if "results" in r_k:
            continue
        print('"'+r_k+'":', end='')
        print(json.dumps(camelize(r_v), indent=None, sort_keys=True, default=str), end=",")
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




