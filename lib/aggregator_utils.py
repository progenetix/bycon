import re, requests, json, sys, datetime, argparse, urllib.parse, time
from os import path, environ, pardir
from copy import deepcopy
from liftover import get_lifter
from humps import camelize
from cgi_parsing import test_truthy

"""
http://progenetix.test/cgi/bycon/beaconServer/aggregator.py?requestedGranularity=boolean&limit=1000&skip=0&datasetIds=progenetix&assemblyId=GRCh38&referenceName=refseq%3ANC_000009.12&variantType=EFO%3A0030067&filterLogic=AND&includeDescendantTerms=True&start=21000000&start=21975098&end=21967753&end=23000000&filters=NCIT%3AC3058
"""

################################################################################

def set_dataset_id(pvs, ext_defs, ds_id):

    if len(ds_id) < 1:

        return pvs

    if "dataset_ids" in ext_defs["parameter_map"]:
        pvs.update({ ext_defs["parameter_map"]["dataset_ids"].get("remap", "dataset_ids"): ds_id})
        return pvs

    if ext_defs.get("camelize", True) is True: 
        pvs.update({ camelize("dataset_ids"): ds_id})
    else:
        pvs.update({ "dataset_ids": ds_id})

    return pvs

################################################################################

def set_default_values(pvs, ext_defs, byc):

    # adding the parameters with defaults defined in the mappings

    for v_p_k, v_p_v in ext_defs["parameter_map"].items():
        if "default" in v_p_v:
            pvs.update({v_p_v["remap"]: v_p_v["default"]})
    return pvs

################################################################################

def remap_parameters_values(pvs, ext_defs, byc):

    # adding the parameters defined in the mappings
    # TODO: de-convolute; maybe by explicitely having a remap method for each
    #       re-mappable parameter instead of this loop & specials mix

    v_rs_chros = byc["variant_definitions"]["chro_aliases"]
    v_states = byc["variant_definitions"]["variant_state_VCF_aliases"]
    v_p_defs = byc["variant_definitions"]["parameters"]
    service_defaults = byc["service_config"]["beacon_params"].get("defaults", {})

    form_p = deepcopy(byc["form_data"])

    target_assembly = service_defaults.get("assembly_id", "GRCh38")
    if "assembly_id" in ext_defs["parameter_map"]:
        target_assembly = ext_defs["parameter_map"]["assembly_id"].get("value", "GRCh38")

    chro = v_rs_chros.get( form_p.get("reference_name", "NA"), "NA") 

    for v_p_k in v_p_defs.keys():

        if not v_p_k in form_p.keys():
            continue
        val = form_p[v_p_k]
        if v_p_k in ext_defs["parameter_map"].keys():
            v_p_v = ext_defs["parameter_map"][v_p_k]

            if "replace" in v_p_v:
                val = re.sub(v_p_v["replace"][0], v_p_v["replace"][1], val)

            if "reference_name" in v_p_k:
                if "chro" in v_p_v.get("reference_style", ""):
                    val = chro

            if "variant_type" in v_p_k:
                if "VCF" in v_p_v.get("variant_style", "VCF"):
                    if val in v_states:
                        val = v_states[val]

            if "variant_type" in v_p_k:
                if "VCF" in v_p_v.get("variant_style", "VCF"):
                    if val in v_states:
                        val = v_states[val]

            elif "start" in v_p_k or "end" in v_p_k:
                val[0] = int(val[0]) + int(v_p_v.get("shift", 0))
                
                if not "38" in target_assembly:
                    val = lift_positions(target_assembly, chro, val, byc)

            if "array" in v_p_defs[v_p_k].get("type", "string"):
                val = ",".join(map(str, val))

            pvs.update({v_p_v["remap"]: val})

    return pvs

################################################################################

def lift_positions(target_assembly, chro, val, byc):

    l_o_o = byc["service_config"]["liftover_options"]
    s_a = byc["service_config"]["beacon_params"]["defaults"]["assembly_id"]

    # TODO: error, conversion feedback ...
    if target_assembly in l_o_o["supported_sources"].keys():
        return val

    if not target_assembly in l_o_o["supported_targets"].keys():
        return val

    # could be hardcoded; will error out if wrong config
    # a bit of a preparation for swapping input assemblies
    s_l_o_k = l_o_o["supported_sources"][s_a]

    lifted = []

    t_l_o_k = l_o_o["supported_targets"][target_assembly]

    converter = get_lifter(s_l_o_k, t_l_o_k)
    for v in val:
        lifted.append(converter[chro][int(v)][0][1])

    return lifted

################################################################################

def add_parameter_values(pvs, ext_defs, byc):

    # adding the parameters which stay _as is_

    form_p = deepcopy(byc["form_data"])
    v_p_defs = byc["variant_definitions"]["parameters"]
    
    for v_p_k in v_p_defs.keys():
        if not v_p_k in form_p.keys():
            continue
        if v_p_k in ext_defs["parameter_map"].keys():
            continue
        val = form_p[v_p_k]
        if "array" in v_p_defs[v_p_k].get("type", "string"):
            val = ",".join(map(str, val))
        if ext_defs.get("camelize", True) is True: 
            v_p_k = camelize(v_p_k)
        
        pvs.update({v_p_k: val})

    return pvs

################################################################################

def remap_min_max_positions(pvs, ext_defs, byc):

    # special mapping of start | end values for bracket queries to the `startMin`
    # format used in v0.4 / v1 

    form_p = deepcopy(byc["form_data"])

    if ext_defs.get("pos_min_max_remaps", False) is not True:
        return pvs

    if not "start" in form_p or not "end" in form_p:
        return pvs

    if len(form_p["start"]) != 2 or len(form_p["end"]) != 2:
        return pvs

    pvs.update({
        "startMin": form_p["start"][0],
        "startMax": form_p["start"][1],
        "endMin": form_p["end"][0],
        "endMax": form_p["end"][1]
    })

    pvs.pop("start", None)
    pvs.pop("end", None)

    return pvs

################################################################################

def set_fixed_values(pvs, ext_defs, byc):

    for v_p_k, v_p_v in ext_defs["parameter_map"].items():
        if "value" in v_p_v:
            pvs.update({v_p_v["remap"]: v_p_v["value"]})
    return pvs

################################################################################

def retrieve_beacon_response(url, byc):

    try:
        return requests.get(url, headers={ "Content-Type" : "application/json"}, timeout=byc["service_config"]["request_timeout"]).json()
    except requests.exceptions.RequestException as e:
        return { "error": e }

################################################################################

def format_response(r, url, ext_defs, ds_id, byc):

    summary_k = "responseSummary"
    if "response_summary" in ext_defs["response_map"].keys():
        summary_k = ext_defs["response_map"]["response_summary"].get("remap", summary_k)

    if "_root_" in summary_k:
        b_resp = r
    else:
        b_resp = r.get(summary_k, {})

    r = {
            "id": ext_defs["id"],
            "dataset_id": ds_id,
            "api_version": ext_defs.get("api_version", None),
            "exists": test_truthy(b_resp.get("exists", False)),
            "info": deepcopy(ext_defs.get("info", {})),
            "error": str(r.get("error", None)) # str to avoid re-interpretation of code
        }
    r["info"].update({
        "query_url": urllib.parse.unquote(url),
        "query_url_encoded": urllib.parse.quote(url)
    })

    return r

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
