import cgi, cgitb
import re, yaml
import logging

from os import path as path
from os import environ
from urllib.parse import urlparse
  
################################################################################

def beacon_get_endpoint(**byc):

    endpoint = "/"

    url_comps = urlparse( environ.get('REQUEST_URI') )
    for p in byc["beacon_paths"].keys():
        if p == url_comps.path:
            return p

    return endpoint

################################################################################

def parse_endpoints(**byc):

    endpoint_pars = { "queries": {}, "response": None }

    url_comps = urlparse( environ.get('REQUEST_URI') )
    ep = url_comps.path
    
    if not ep:
        return(endpoint_pars)

    path_items = [ x for x in ep.split('/') if x ]

    if len(path_items) < 1:
        return(endpoint_pars)

    scope = path_items[0]
    scope = scope.replace("g_variants", "variants")
    endpoint_pars.update( { "response": scope } )

    if len(path_items) < 2:
        return(endpoint_pars)

    endpoint_pars.update( { "queries": { scope: { "id": path_items[1] } } } )

    if len(path_items) < 3:
        return(endpoint_pars)

    response = path_items[2]
    response = response.replace("g_variants", "variants")

    endpoint_pars.update( { "response": response } )

    return endpoint_pars

    # starting with the paths with most components


################################################################################
