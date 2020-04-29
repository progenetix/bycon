import cgi, cgitb
import json
import os, re
from urllib.parse import urlparse

################################################################################

def cgi_parse_query():

    form_data = cgi.FieldStorage()
    return(form_data)

################################################################################

def cgi_parse_path_params( script_name ):
    """
    URL components after the script name are deparsed into parameters.
    """

    path_pars =  { }
    path_items = [ ]

    url_comps = urlparse( os.environ.get('REQUEST_URI') )
    if type(url_comps.path) == str:
        path_items = re.split(r'\/|\&', url_comps.path)
    par_re = re.compile( r'^(\w.*?)\=(\w.*?)$')

    if not script_name in path_items:
        return(path_pars)

    i = 0
    p_i = 255
    for p in path_items:
        i += 1
        if p == script_name:
            p_i = i
        if i >= p_i:
            try:
                if par_re.match( path_items[ i ] ):
                    par, val = par_re.match( path_items[ i ] ).group(1,2)
                    path_pars[ par ] = val
            except Exception:
                pass

    return(path_pars)

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

def cgi_print_json_callback(callback, data):
    print('Content-Type: application/json')
    print()
    print(callback+'({"data":'+json.dumps(data, default=str)+"});\n")
    exit()

################################################################################

