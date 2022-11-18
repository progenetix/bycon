#!/usr/local/bin/python3

import re, json
from os import path, environ, pardir
from copy import deepcopy
import sys, datetime, argparse

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from beaconServer import *

"""podmd

* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgxcohort-TCGAcancers
* https://progenetix.org/cgi/bycon/services/intervalFrequencies.py/?output=pgxseg&datasetIds=progenetix&filters=NCIT:C7376

https://cancer.sanger.ac.uk/api/ga4gh/beacon?allele=A&chrom=7&dataset=cosmic&format=json&pos=140753336&ref=38
http://progenetix.test/services/aggregator/debug=1
http://progenetix.test/cgi/bycon/beaconServer/aggregator.py?debug=1&reference_name=7&start=140753335&alternate_bases=A&assemblyId=GRCh38&responseEntityId=genomicVariant

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

    v_d = byc["variant_definitions"]
    v_p_defs = v_d["parameters"]

    byc["service_response"]["meta"]["received_request_summary"]["requested_granularity"] ="boolean"
    check_switch_to_boolean_response(byc)
    byc["service_response"].update({"response": { "response_sets": [] }})

    for b in byc["service_config"]["selected_beacons"]:
        ext_defs = byc["service_config"]["beacon_params"][b]
        form_p = deepcopy(byc["variant_pars"])
        v_q_p = []

        for v_p_k, v_p_v in ext_defs["parameter_map"].items():
            if "default" in v_p_v:
                v_q_p.append("{}={}".format(v_p_v["remap"], v_p_v["default"]))

        for v_p_k in v_p_defs.keys():
            if not v_p_k in form_p.keys():
                continue
            val = form_p[v_p_k]
            if v_p_k in ext_defs["parameter_map"].keys():
                v_p_v = ext_defs["parameter_map"][v_p_k]
                if "default" in v_p_v:
                    continue
                if "replace" in v_p_v:
                    val = re.sub(v_p_v["replace"][0], v_p_v["replace"][1], val)
                if "start" in v_p_k or "end" in v_p_k:
                    val[0] += int(v_p_v.get("shift", 0))
                if "array" in v_p_defs[v_p_k].get("type", "string"):
                    val = ",".join(map(str, val))
                if "refseq:" in val:
                    val = v_d["refseq_chronames"][ val ]
                v_q_p.append("{}={}".format(v_p_v["remap"], val))
            else:
                if "array" in v_p_defs[v_p_k].get("type", "string"):
                    val = ",".join(map(str, val))
                if ext_defs.get("camelize", True) is True: 
                    v_p_k = camelize(v_p_k)
                v_q_p.append("{}={}".format(v_p_k, val))

        url = "{}{}".format(ext_defs["base_url"], "&".join(v_q_p))
        # prjsoncam(url)
        try:
            response = requests.get(url, timeout=byc["service_config"]["request_timeout"]).json()
        except requests.exceptions.RequestException as e:
            response = { "error": e }

        summary_k = "responseSummary"
        if "response_summary" in ext_defs["response_map"].keys():
            summary_k = ext_defs["response_map"]["response_summary"].get("remap", summary_k)

        b_resp = response.get(summary_k, {})
        byc["service_response"]["response"]["response_sets"].append(
            {
                "id": ext_defs["id"],
                "api_version": ext_defs.get("api_version", None),
                "exists": test_truthy(b_resp.get("exists", False)),
                "info": {
                    "query_url": url
                },
                "error": response.get("error", None)
            }
        )

    for r in byc["service_response"]["response"]["response_sets"]:
        if r["exists"] is True:
            byc["service_response"]["response_summary"].update({"exists": True})
            continue

    cgi_print_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
