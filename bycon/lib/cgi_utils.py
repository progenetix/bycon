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

def cgi_print_text_response(form_data, data, status_code):

    print('Content-Type: text')
    print('status:'+str(status_code))
    print()
    print(data+"\n")
    exit()

################################################################################

def cgi_print_json_response(form_data, response, status_code):

    if "callback" in form_data:
        data = form_data.getvalue("callback")+'('+json.dumps(response, default=str)+")\n"
        cgi_print_text_response(form_data, data, status_code)

    if "responseType" in form_data:
        r_t = form_data.getvalue("responseType")
        if "text" in r_t:
            if "data" in response:
                response = response["data"]
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

    if "data" in response:
        if "responseFormat" in form_data:
            r_f = form_data.getvalue("responseFormat")
            if "simple" in r_f:
                response = response["data"]

    print('Content-Type: application/json')
    print('status:'+str(status_code))
    print()
    print(json.dumps(response, indent=4, sort_keys=True, default=str)+"\n")
    exit()

################################################################################
