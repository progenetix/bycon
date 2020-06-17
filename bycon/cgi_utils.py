import cgi, cgitb
import json
from os import environ as environ
import re
from urllib.parse import urlparse

################################################################################

def cgi_parse_query():

    form_data = cgi.FieldStorage()

    if "debug" in form_data:
        print('Content-Type: text')
        print()
        cgitb.enable()
    else:
        pass

    return(form_data)

################################################################################

def beacon_get_endpoint(**byc):

    url_comps = urlparse( environ.get('REQUEST_URI') )
    for p in byc["beacon_paths"].keys():
        if p == url_comps.path:
            return(p)

################################################################################


def cgi_parse_path_params( script_name ):
    """
    #### `cgi_parse_path_params`

    URL components after the script name are deparsed into parameters.

    This option is skipped if a query string exists to avoid parameter
    collisions.

    Splitting for list parameters (e.g. `filters`) is performed at a later
    stage.
    """

    path_pars =  { }
    path_items = [ ]

    url_comps = urlparse( environ.get('REQUEST_URI') )
    if url_comps.query:
        return(path_pars)
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
    
    if "debug" in path_pars:
        if path_pars["debug"]:
            print('Content-Type: text')
            print()

            cgitb.enable()
        else:
            pass
    else:
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

