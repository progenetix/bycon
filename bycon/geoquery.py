import cgi, cgitb
import re, yaml
import logging
import sys
from bson.son import SON

from .cgi_utils import *

################################################################################

def geo_query( geojsonpar, **byc ):

    geo_pars = { }
    geo_query = { }
    g_q_k = byc["geolocations"]["request_types"]["geoquery"]["all_of"]
    g_p_defs = byc["geolocations"]["parameters"]

    for g_k in g_q_k:
        g_default = None
        if "default" in g_p_defs[ g_k ]:
            g_default = g_p_defs[ g_k ][ "default" ]
        g_v = byc["form_data"].getvalue(g_k, g_default)
        if not g_v:
            continue
        if not re.compile( g_p_defs[ g_k ][ "pattern" ] ).match( str( g_v ) ):
            continue
        if "float" in g_p_defs[ g_k ][ "type" ]:
            geo_pars[ g_k ] = float(g_v)
        else:
            geo_pars[ g_k ] = g_v

    if len( geo_pars ) < len( g_q_k ):
        return geo_query, geo_pars

    geo_query = {
        geojsonpar: {
            '$near': SON(
                [
                    (
                        '$geometry', SON(
                            [
                                ('type', 'Point'),
                                ('coordinates', [
                                    geo_pars["geolongitude"],
                                    geo_pars["geolatitude"]
                                ])
                            ]
                        )
                    ),
                    ('$maxDistance', geo_pars["geodistance"])
                ]
            )
        }
    }

    return geo_query, geo_pars

################################################################################
