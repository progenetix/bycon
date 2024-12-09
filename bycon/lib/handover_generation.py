import re
from pymongo import MongoClient
from pathlib import Path
from os import environ, pardir, path
import sys

from bycon_helpers import hex_2_rgb, prdbug, select_this_server
from config import *
from variant_mapping import ByconVariant

################################################################################

def dataset_response_add_handovers(ds_id, datasets_results):
    """
    """
    b_h_o = [ ]
    if BYC_PARS.get("include_handovers", True) is not True:
        return b_h_o
    if not ds_id in BYC["dataset_definitions"]:
        return b_h_o
    skip = BYC_PARS.get("skip")
    limit = BYC_PARS.get("limit")
    e_t = BYC["response_entity"].get("response_entity_id", "___none___")
    h_o_server = select_this_server()
    h_o_types = BYC["handover_definitions"]["h->o_types"]
    ds_h_o = BYC["dataset_definitions"][ds_id].get("handoverTypes", h_o_types.keys())
    ds_res_k = list(datasets_results[ds_id].keys())

    prdbug(f'... pre handover {ds_res_k}')

    for h_o_t, h_o_defs in h_o_types.items():
        if h_o_t not in ds_h_o:
            continue

        h_o_k = h_o_types[ h_o_t ].get("h->o_key", "___none___")
        if not (h_o := datasets_results[ds_id].get(h_o_k)):
            continue
        # testing if this handover is active for the specified dataset      
        if (target_count := h_o.get("target_count", 0)) < 1:
            continue

        accessid = h_o["id"]
        h_o_r = {
            "handover_type": h_o_defs.get("handoverType", {}),
            "info": {
                "content_id": h_o_t,
                "count": target_count
            },
            "note": h_o_defs[ "note" ],
            "url": __handover_create_url(h_o_server, h_o_defs, ds_id, accessid)
        }

        # TODO: needs a new schema to accommodate this not as HACK ...
        # the phenopackets URL needs matched variants, which it wouldn't know about ...
        if "phenopackets" in h_o_t:
            if "variants.id" in datasets_results[ds_id].keys():
                h_o_r["url"] += f'&variantsaccessid={datasets_results[ds_id]["variants.id"]["id"]}'

        if "url" in h_o_r:
            b_h_o.append( h_o_r )

    return b_h_o


################################################################################

def __handover_create_url(h_o_server, h_o_defs, ds_id, accessid):
    if not (addr := h_o_defs.get("script_path_web")):
        return ""
    server = "" if "http" in addr else h_o_server
    url = f'{server}{addr}?datasetIds={ds_id}&accessid={accessid}'
    for p in ["plotType", "output"]:
        if (v := h_o_defs.get(p)):
            url += f"&{p}={v}"
    return url


