import cgi, cgitb
import json
import re

################################################################################

def cgi_parse_query():

    form_data = cgi.FieldStorage()

    if "debug" in form_data:
        print('Content-Type: text')
        print()
        cgitb.enable()
    else:
        pass

    return form_data

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

def cgi_print_text_response(data):

    print('Content-Type: text')
    print()
    print(data+"\n")
    exit()

################################################################################

def cgi_print_svg_response(data):

    print('Content-Type: image/svg')
    print()
    print(data+"\n")
    exit()

################################################################################

def cgi_print_json_response(form_data, response):

    if "callback" in form_data:
        print('Content-Type: text')
        print()
        print(form_data.getvalue("callback")+'('+json.dumps(response, default=str)+")\n")
        exit()

    if "data" in response:
        if "responseFormat" in form_data:
            r_f = form_data.getvalue("responseFormat")
            if "simple" in r_f:
                response = response["data"]

    print('Content-Type: application/json')
    print()
    print(json.dumps(response, indent=4, sort_keys=True, default=str)+"\n")
    exit()

################################################################################
