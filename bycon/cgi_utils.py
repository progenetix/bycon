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

def cgi_print_json_response(**data):

    print('Content-Type: application/json')
    print()
    print(json.dumps(data, indent=4, sort_keys=True, default=str)+"\n")
    exit()

################################################################################

def cgi_print_json_callback(callback, **data):

    print('Content-Type: application/json')
    print()
    print(callback+'('+json.dumps(data, default=str)+")\n")
    exit()

################################################################################
