import cgi, cgitb
import re, yaml
import logging
import sys
from bson.son import SON

from .cgi_utils import *

################################################################################

def geo_query( **byc ):

    geo_pars = { }
    geo_query = { }
    g_q_k = byc["extended_defs"]["request_types"]["geoquery"]["all_of"]
    g_p_defs = byc["extended_defs"]["parameters"]

    for g_k in g_q_k:
        g_default = None
        if "default" in g_p_defs[ g_k ]:
            g_default = g_p_defs[ g_k ][ "default" ]
        g_v = byc["form_data"].getvalue(g_k, g_default)
        if not g_v:
            continue
        if not re.compile( g_p_defs[ g_k ][ "pattern" ] ).match( str( g_v ) ):
            continue
        geo_pars[ g_k ] = g_v

    if len( geo_pars ) < len( g_q_k ):
        return geo_query

    g_lat = float(geo_pars["geolatitude"])
    g_long = float(geo_pars["geolongitude"])
    g_dist = float(geo_pars["geodistance"])

    geo_query = {"provenance.geo.geojson": {'$near': SON([('$geometry', SON([('type', 'Point'), ('coordinates', [g_long, g_lat])])), ('$maxDistance', g_dist)])}}

    return geo_query

################################################################################
