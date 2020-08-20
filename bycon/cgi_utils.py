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

def cgi_exit_on_error(shout):

    print("Content-Type: text")
    print()
    print(shout)
    exit()

################################################################################

def cgi_print_json_response(data):

    print('Content-Type: application/json')
    print()
    print(json.dumps(data, indent=4, sort_keys=True, default=str))
    exit()

################################################################################

def cgi_print_json_callback(callback, name, data):

    print('Content-Type: application/json')
    print()
    print(callback+'({"'+name+'":'+json.dumps(data, default=str)+"});\n")
    exit()

################################################################################

