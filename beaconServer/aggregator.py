#!/usr/local/bin/python3

import re, json, sys, datetime, argparse, urllib.parse, time
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

TODO:

* move from the "parameters per instance" to "parameters per version"
    - this may not work if those instances take "liberties" with their parameters ...
* split into different functions
    - a main aggregator which handles i/o for a list of beacons (i.e. the original)
    - an option to have it just return the query URLs w/o executing them, e.g. as handovers
    - a single query processor, taking the modified query url as input, retrieving the
      query & providing the response in the standard v2 format
* provide a prototype front-end which parses the list of transformed queries & uses
  the retriever to asynchronously populate the front-end, and to provide an aggregate
  summary
* message if query (e.g. brackets ...) is not supported
* liftover examples ... https://pypi.org/project/liftover/ 


#### Tests

* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&filters=NCIT:C7376,PMID:22824167
* https://progenetix.org/services/intervalFrequencies/?datasetIds=progenetix&id=pgxcohort-TCGAcancers
* https://progenetix.org/cgi/bycon/services/intervalFrequencies.py/?output=pgxseg&datasetIds=progenetix&filters=NCIT:C7376
* http://progenetix.org/beacon/aggregator/?requestedGranularity=boolean&referenceBases=G&alternateBases=A&limit=1000&skip=0&datasetIds=progenetix&assemblyId=GRCh38&referenceName=refseq%3ANC_000017.11&filterLogic=AND&includeDescendantTerms=True&start=7577120

* https://cancer.sanger.ac.uk/api/ga4gh/beacon?allele=A&chrom=7&dataset=cosmic&format=json&pos=140753336&ref=38
* http://progenetix.org/services/aggregator/debug=1
* http://progenetix.org/cgi/bycon/beaconServer/aggregator.py?debug=1&reference_name=7&start=140753335&alternate_bases=A&assemblyId=GRCh38&responseEntityId=genomicVariant

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

    b_p = byc["service_config"]["beacon_params"]["instances"]

    byc["service_response"]["meta"]["received_request_summary"]["requested_granularity"] ="boolean"
    check_switch_to_boolean_response(byc)
    byc["service_response"].update({"response": { "response_sets": [] }})

    for b in byc["service_config"]["selected_beacons"]:

        ext_defs = b_p[b]

        for ds_id in ext_defs.get("dataset_ids", [""]):

            byc["form_data"].update({"dataset_ids": [ds_id]})

            pvs = {}

            """
            Values (for the respective parameter names) are processed step-wise:
            1. defaults are read in
            2. form values w/ remap infor are processed
            3. the non-remapped p=v are added
            4. fixed `value` parameters are (over-)written
            TODO: should we be explicit in parsing selected parameters,
            i.e. evaluating all (relevant) v2 ones?
            """

            _set_dataset_id(pvs, ext_defs, ds_id)
            _set_default_values(pvs, ext_defs, byc)
            _remap_parameters_values(pvs, ext_defs, byc)
            _add_parameter_values(pvs, ext_defs, byc)
            _remap_min_max_positions(pvs, ext_defs, byc)
            _set_fixed_values(pvs, ext_defs, byc)

            url = "{}{}".format(ext_defs["base_url"], urllib.parse.urlencode(pvs))
 
            resp_start = time.time()
            r = _retrieve_beacon_response(url)
            resp_end = time.time()
            # prjsoncam(r)
            r_f = _format_response(r, url, ext_defs, ds_id, byc)
            r_f["info"].update({"response_time": "{}ms".format(round((resp_end - resp_start) * 1000, 0)) })
            byc["service_response"]["response"]["response_sets"].append(r_f)

    for r in byc["service_response"]["response"]["response_sets"]:
        if r["exists"] is True:
            byc["service_response"]["response_summary"].update({"exists": True})
            continue

    cgi_print_response( byc, 200 )

################################################################################

def _set_dataset_id(pvs, ext_defs, ds_id):

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

def _set_default_values(pvs, ext_defs, byc):

    # adding the parameters with defaults defined in the mappings

    for v_p_k, v_p_v in ext_defs["parameter_map"].items():
        if "default" in v_p_v:
            pvs.update({v_p_v["remap"]: v_p_v["default"]})
    return pvs

################################################################################

def _remap_parameters_values(pvs, ext_defs, byc):

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
                    val = _lift_positions(target_assembly, chro, val)

            if "array" in v_p_defs[v_p_k].get("type", "string"):
                val = ",".join(map(str, val))

            pvs.update({v_p_v["remap"]: val})

    return pvs

################################################################################

def _lift_positions(target_assembly, chro, val):

    # TODO: liftover
    if "38" in target_assembly:
        return val

    lifted = []

    if "19" in target_assembly or "37" in target_assembly:

        converter = get_lifter('hg38', 'hg19')
        for v in val:
            lifted.append(converter[chro][int(v)][0][1])

        return lifted

    return val

################################################################################

def _add_parameter_values(pvs, ext_defs, byc):

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

def _remap_min_max_positions(pvs, ext_defs, byc):

    # special mapping of start | end values for bracket queries to the `startMin`
    # format used in v0.4 / v1 

    form_p = deepcopy(byc["form_data"])

    if ext_defs.get("pos_min_max_remaps", False) is not True:
        return pvs

    if len(form_p["start"]) is not 2 or len(form_p["end"]) is not 2:
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

def _set_fixed_values(pvs, ext_defs, byc):

    for v_p_k, v_p_v in ext_defs["parameter_map"].items():
        if "value" in v_p_v:
            pvs.update({v_p_v["remap"]: v_p_v["value"]})
    return pvs

################################################################################

def _retrieve_beacon_response(url):

    try:
        return requests.get(url, headers={ "Content-Type" : "application/json"}, timeout=byc["service_config"]["request_timeout"]).json()
    except requests.exceptions.RequestException as e:
        return { "error": e }

################################################################################

def _format_response(r, url, ext_defs, ds_id, byc):

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
    r["info"].update({"query_url": urllib.parse.unquote(url)})

    return r

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
