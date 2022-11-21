#!/usr/local/bin/python3

import re, json, sys, datetime, argparse
from os import path, environ, pardir
from copy import deepcopy
from liftover import get_lifter

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd

This app is used to prototype federated Beacon queries through
translating / sending / retrieving / converting Beacon queries in v2 format to
the format of the respective Beacon instances.

Queries are expected in the GRCh38 Beacon v2 format with parameters:

* `referenceName` as either `refseq:NC_...` or just `17` etc.
* `start`
* `alternateBases`
* `referenceBases` aren't supported by most olf beacons?


* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgxcohort-TCGAcancers
* https://progenetix.org/cgi/bycon/services/intervalFrequencies.py/?output=pgxseg&datasetIds=progenetix&filters=NCIT:C7376

https://cancer.sanger.ac.uk/api/ga4gh/beacon?allele=A&chrom=7&dataset=cosmic&format=json&pos=140753336&ref=38
http://progenetix.test/services/aggregator/debug=1
http://progenetix.test/cgi/bycon/beaconServer/aggregator.py?debug=1&reference_name=7&start=140753335&alternate_bases=A&assemblyId=GRCh38&responseEntityId=genomicVariant


#### TODO

* message if query (e.g. brackets ...) is not supported
* liftover examples ... https://pypi.org/project/liftover/ 

"""

################################################################################
################################################################################
################################################################################

def main():

    aggregator()
   
################################################################################

def beaconAggregator():
    aggregator()

################################################################################

def aggregator():

    initialize_service(byc)
    parse_filters(byc)
    parse_variant_parameters(byc)
    generate_genomic_intervals(byc)
    create_empty_service_response(byc)    

    cgi_break_on_errors(byc)

    if "selected_beacons" in byc["form_data"]:
        byc["service_config"].update({"selected_beacons": byc["form_data"]["selected_beacons"]})

    b_p = byc["service_config"]["beacon_params"]["parameters"]

    byc["service_response"]["meta"]["received_request_summary"]["requested_granularity"] ="boolean"
    check_switch_to_boolean_response(byc)
    byc["service_response"].update({"response": { "response_sets": [] }})

    for b in byc["service_config"]["selected_beacons"]:

        ext_defs = b_p[b]
        pvs = {}

        """
        Values (for the respective parameter names) are processed step-wise:
        1. defaults are read in
        2. form values w/ remap infor are processed
        3. the non-remapped p=v are added
        4. fixed `value` parameters are (over-)written
        """

        _set_default_values(pvs, ext_defs, byc)
        _remap_parameters_values(pvs, ext_defs, byc)
        _add_parameter_values(pvs, ext_defs, byc)
        _set_fixed_values(pvs, ext_defs, byc)
        _stringify_query(pvs)

        url = "{}{}".format(ext_defs["base_url"], _stringify_query(pvs))

        r = _retrieve_beacon_response(url)
        r_f = _format_response(r, url, ext_defs, byc)
        byc["service_response"]["response"]["response_sets"].append(r_f)

    for r in byc["service_response"]["response"]["response_sets"]:
        if r["exists"] is True:
            byc["service_response"]["response_summary"].update({"exists": True})
            continue

    cgi_print_response( byc, 200 )

################################################################################

def _set_default_values(pvs, ext_defs, byc):

    for v_p_k, v_p_v in ext_defs["parameter_map"].items():
        if "default" in v_p_v:
            pvs.update({v_p_v["remap"]: v_p_v["default"]})
    return pvs

################################################################################

def _remap_parameters_values(pvs, ext_defs, byc):

    v_rs_chros = byc["variant_definitions"]["chro_aliases"]
    v_p_defs = byc["variant_definitions"]["parameters"]
    form_p = deepcopy(byc["variant_pars"])

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
                    if val in v_rs_chros:
                        val = v_rs_chros[val]

            elif "start" in v_p_k or "end" in v_p_k:
                val[0] += int(v_p_v.get("shift", 0))
            if "array" in v_p_defs[v_p_k].get("type", "string"):
                val = ",".join(map(str, val))

            pvs.update({v_p_v["remap"]: val})

    return pvs

################################################################################

def _add_parameter_values(pvs, ext_defs, byc):

    form_p = deepcopy(byc["variant_pars"])
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

def _set_fixed_values(pvs, ext_defs, byc):

    for v_p_k, v_p_v in ext_defs["parameter_map"].items():
        if "value" in v_p_v:
            pvs.update({v_p_v["remap"]: v_p_v["value"]})
    return pvs

################################################################################

def _stringify_query(pvs):

    return "&".join("{}={}".format(k, v) for k, v in pvs.items())

################################################################################

def _retrieve_beacon_response(url):

    try:
        return requests.get(url, timeout=byc["service_config"]["request_timeout"]).json()
    except requests.exceptions.RequestException as e:
        return { "error": e }

################################################################################

def _format_response(r, url, ext_defs, byc):

    summary_k = "responseSummary"
    if "response_summary" in ext_defs["response_map"].keys():
        summary_k = ext_defs["response_map"]["response_summary"].get("remap", summary_k)

    b_resp = r.get(summary_k, {})
    r = {
            "id": ext_defs["id"],
            "api_version": ext_defs.get("api_version", None),
            "exists": test_truthy(b_resp.get("exists", False)),
            "info": {
                "query_url": url
            },
            "error": r.get("error", None)
        }

    return r

################################################################################
################################################################################

if __name__ == '__main__':
    main()
