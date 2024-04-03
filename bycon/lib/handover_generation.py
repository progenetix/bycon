import re
from pymongo import MongoClient
from pathlib import Path
from os import environ, pardir, path
import sys

from bycon_helpers import hex_2_rgb, prdbug, select_this_server
from config import *
from variant_mapping import ByconVariant

################################################################################

def dataset_response_add_handovers(ds_id, byc):
    """podmd
    podmd"""
    b_h_o = [ ]
    if BYC_PARS.get("include_handovers", True) is not True:
        return b_h_o
    if not ds_id in byc["dataset_definitions"]:
        return b_h_o
    skip = BYC_PARS.get("skip")
    limit = BYC_PARS.get("limit")
    h_o_server = select_this_server(byc)
    h_o_types = byc["handover_definitions"]["h->o_types"]
    ds_h_o = byc["dataset_definitions"][ds_id].get("handoverTypes", h_o_types.keys())
    ds_res_k = list(byc["dataset_results"][ds_id].keys())

    prdbug(f'... pre handover {ds_res_k}')

    for h_o_t, h_o_defs in h_o_types.items():
        if h_o_t not in ds_h_o:
            continue

        h_o_k = h_o_types[ h_o_t ].get("h->o_key", "___none___")
        if not (h_o := byc["dataset_results"][ds_id].get(h_o_k)):
            continue
        # testing if this handover is active for the specified dataset      
        if (target_count := h_o.get("target_count", 0)) < 1:
            continue

        accessid = h_o["id"]
        h_o_r = {
            "handover_type": h_o_defs.get("handoverType", {}),
            "info": { "content_id": h_o_t},
            "note": h_o_defs[ "note" ],
            "url": __handover_create_url(h_o_server, h_o_defs, ds_id, accessid)
        }

        # TODO: needs a new schema to accommodate this not as HACK ...
        # the phenopackets URL needs matched variants, which it wouldn't know about ...
        if "phenopackets" in h_o_t:
            if "variants._id" in byc["dataset_results"][ds_id].keys():
                h_o_r["url"] += f'&variantsaccessid={byc["dataset_results"][ds_id]["variants._id"]["id"]}'

        e_t = byc["response_entity"].get("response_entity_id", "___none___")
        p_e = h_o_defs.get("paginated_entities", [])

        if e_t in p_e or "all" in p_e:
            # avoiding endless loop
            if limit < 1:
                break
            h_o_r.update({"pages":[]})
            p_f = 0
            p_t = p_f + limit
            p_s = 0
            while p_f < target_count + 1:
                if target_count < p_t:
                    p_t = target_count
                l = f"{p_f + 1}-{p_t}"
                u = __handover_create_url(h_o_server, h_o_defs, ds_id, accessid, p_s, limit)
                h_o_r["pages"].append( {
                    "handover_type": {"id": h_o_defs["handoverType"][ "id" ],"label": l }, 
                    "info": { "content_id": h_o_t},
                    "url": u
                } )
                p_s += 1
                p_f += limit
                p_t = p_f + limit
            h_o_r["url"] += f'&skip={skip}&limit={limit}'
        if "url" in h_o_r:
            b_h_o.append( h_o_r )

    return b_h_o


################################################################################

def __handover_create_url(h_o_server, h_o_defs, ds_id, accessid, skip=BYC_PARS.get("skip"), limit=BYC_PARS.get("limit")):
    if not (addr := h_o_defs.get("script_path_web")):
        return ""
    server = "" if "http" in addr else h_o_server
    url = f'{server}{addr}?datasetIds={ds_id}&accessid={accessid}&skip={skip}&limit={limit}'
    for p in ["method", "output", "plotType", "requestedSchema"]:
        if not (v := h_o_defs.get(p)):
            continue
        url += f"&{p}={v}"
    url += h_o_defs.get("url_opts", "")
    return url


