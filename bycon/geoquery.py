import cgi, cgitb
import re, yaml
import logging
import sys
from bson.son import SON

from .cgi_utils import *

################################################################################

def geo_query( **byc ):

    geo_q = { }
    geo_pars = { }

    if not "geolocations" in byc:
        return geo_q, geo_pars

    g_p_defs = byc["geolocations"]["parameters"]
    g_p_rts = byc["geolocations"]["request_types"]
    geo_root = byc["geolocations"]["geo_root"]

    req_type = ""
    for rt in g_p_rts:
        g_p = { }
        g_q_k = g_p_rts[ rt ]["all_of"]
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
                g_p[ g_k ] = float(g_v)
            else:
                g_p[ g_k ] = g_v

        if len( g_p ) < len( g_q_k ):
            continue

        req_type = rt
        geo_pars = g_p

    if "city" in req_type:
        geo_q = return_geo_city_query(geo_root, geo_pars)

    if "geoquery" in req_type:
        geo_q = return_geo_longlat_query(geo_root, geo_pars)

    return geo_q, geo_pars

################################################################################

def return_geo_city_query(geo_root, geo_pars):

    if len(geo_root) > 0:
        citypar = ".".join( (geo_root, "city") )
    else:
        citypar = "city"

    geo_q = { citypar: re.compile( r'^'+geo_pars["city"], re.IGNORECASE ) }

    return geo_q

################################################################################

def return_geo_longlat_query(geo_root, geo_pars):

    if len(geo_root) > 0:
        geojsonpar = ".".join( (geo_root, "geojson") )
    else:
        geojsonpar = "geojson"

    geo_q = {
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

    return geo_q

################################################################################
