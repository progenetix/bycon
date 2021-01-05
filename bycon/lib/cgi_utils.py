import cgi, cgitb
from urllib.parse import urlparse
from os import environ
import json
import re

################################################################################

def set_debug_state():

    if environ.get('REQUEST_URI'):
        if "debug=1" in environ.get('REQUEST_URI'):
            cgitb.enable()
            print('Content-Type: text')
            print()

################################################################################

def cgi_parse_query():

    set_debug_state()

    return cgi.FieldStorage()

################################################################################

def rest_path_value(key):

    url_comps = urlparse( environ.get('REQUEST_URI') )
    p_items = re.split(r'\/|\&', url_comps.path)
    i = 0
    f = ""

    for p in p_items:
        i += 1
        if len(p_items) > i:
            if p == key:
                return p_items[ i ]

    return False

################################################################################

def form_return_listvalue( form_data, parameter ):

    l_v = [ ]
    if len(form_data) > 0:
        if parameter in form_data:
            v = form_data.getlist( parameter )
            if "null" in v:
                v.remove("null")
            if len(v) > 0:
                l_v  = ','.join(v)
                l_v  = l_v .split(',')

    return l_v 

################################################################################

def cgi_print_text_response(form_data, data, status_code):

    print('Content-Type: text')
    print('status:'+str(status_code))
    print()
    print(data+"\n")
    exit()

################################################################################

def cgi_select_data_response(form_data, response, simpledata):

    if "responseFormat" in form_data:
        r_f = form_data.getvalue("responseFormat")
        if "simple" in r_f:
            response = { "data": simpledata }

    return response

################################################################################

def cgi_simplify_response(response):

    if "data" in response:            
        return response["data"]
    elif "response" in response:
        if "results" in response["response"]:
            return response["response"]["results"]

    return response

################################################################################

def cgi_print_json_response(form_data, response, status_code):

    r_f = ""
    r_t = ""

    if "responseType" in form_data:
        r_t = form_data.getvalue("responseType")
    if "responseFormat" in form_data:
        r_f = form_data.getvalue("responseFormat")

    if "callback" in form_data:
        data = form_data.getvalue("callback")+'('+json.dumps(response, default=str)+")\n"
        cgi_print_text_response(form_data, data, status_code)


    # This is a simple "de-jsonify", intended to be used for already
    # pre-formatted list-like items (i.e. lists only containing objects)
    # with simple key-value pairs)
    # TODO: universal text table converter
    if "text" in r_t:
        response = cgi_simplify_response(response)      
        if isinstance(response, dict):
            response = json.dumps(response, default=str)
        if isinstance(response, list):
            l_d = [ ]
            for dp in response:
                v_l = [ ]
                for v in dp.values():
                    v_l.append(str(v))
                l_d.append("\t".join(v_l))
            response = "\n".join(l_d)
        cgi_print_text_response(form_data, response, status_code)

    if "simple" in r_f:
        response = cgi_simplify_response(response)

    print('Content-Type: application/json')
    print('status:'+str(status_code))
    print()
    print(json.dumps(response, indent=4, sort_keys=True, default=str)+"\n")
    exit()

################################################################################



