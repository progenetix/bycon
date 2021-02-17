import cgi
import re, yaml
import logging
from os import path, environ
from urllib.parse import urlparse
  
################################################################################

def beacon_get_endpoint(byc):

    byc.update( { "endpoint": '/' } )

    if not environ.get('REQUEST_URI'):
        return byc

    url_comps = urlparse( environ.get('REQUEST_URI') )

    for p in byc["beacon"]["paths"].keys():
        if p == '/':
            continue
        m = re.compile(r'(^.+?byconplus(\.py)?)?'+p)
        if m.match(url_comps.path):
            return byc.update( { "endpoint": p } )

    return byc

################################################################################

def parse_endpoints(byc):

    byc.update( { "endpoint_pars": _endpoint_response_from_pars( **byc ) } )

    url_comps = urlparse( environ.get('REQUEST_URI') )
    e_path = url_comps.path
    
    if not e_path:
        return byc
 
    if not byc["endpoint"]:
        return byc

    ep = byc["endpoint"].split('/')[1]

    all_path = [ x for x in e_path.split('/') if x ]
    path_items = [ ]

    keep = False
    for p_i in all_path:
        if p_i == ep:
            keep = True
        if keep:
            path_items.append(p_i)

    if len(path_items) < 1:
        return byc

    if not path_items[0] in byc["endpoint"]:
        return byc

    scope = path_items[0]
    scope = scope.replace("g_variants", "variants")
    byc["endpoint_pars"].update( { "response": scope } )

    if len(path_items) < 2:
        return byc

    id_key = "id"
    if scope == "variants":
        id_key = "digest"

    byc["endpoint_pars"].update( { "queries": { scope: { id_key: path_items[1] } } } )

    if len(path_items) < 3:
        return byc

    response = path_items[2]
    response = response.replace("g_variants", "variants")

    byc["endpoint_pars"].update( { "response": response } )

    return byc

################################################################################

def _endpoint_response_from_pars( **byc ):

    colls = byc["config"]["collections"]
    endpoint_pars = { "queries": {}, "response": "" } 

    if not "scope" in byc["form_data"]:
        return endpoint_pars

    scope = byc["form_data"].getvalue("scope")
    scope = scope.replace("g_variants", "variants")
    if scope in colls:
        endpoint_pars.update( { "response": scope } )

        if "id" in byc["form_data"]:
            id_key = "id"
            if scope == "variants":
                id_key = "digest"
            endpoint_pars.update( { "queries": { scope: { id_key: byc["form_data"].getvalue("id") } } } )

    if "response" in byc["form_data"]:
        response = byc["form_data"].getvalue("response")
        response = response.replace("g_variants", "variants")
        if response in colls:
            endpoint_pars.update( { "response": response } )

    return endpoint_pars


