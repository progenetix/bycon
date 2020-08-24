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

def cgi_print_json_response(form_data, **response):

    if "callback" in form_data:
        print('Content-Type: text')
        print()
        print(form_data.getvalue("callback")+'('+json.dumps(response, default=str)+")\n")
        exit()

    print('Content-Type: application/json')
    print()
    print(json.dumps(response, indent=4, sort_keys=True, default=str)+"\n")
    exit()

################################################################################
