import inspect
import re
from deepmerge import always_merger
from os import environ, path

from args_parsing import *
from config import *
from beacon_auth import *
from bycon_helpers import return_paginated_list, prdbug, set_debug_state, test_truthy
from dataset_parsing import select_dataset_ids
from parse_filters_request import parse_filters
from read_specs import update_rootpars_from_local
from parse_variant_request import parse_variants


################################################################################

def set_beacon_defaults(byc):
    defaults: object = BYC["beacon_defaults"].get("defaults", {})
    for d_k, d_v in defaults.items():
        byc.update( { d_k: d_v } )
  

################################################################################

def initialize_bycon_service(byc, service="info"):
    # TODO - streamline, also for services etc.
    defs = BYC["beacon_defaults"]
    b_e_d = defs.get("entity_defaults", {})
    s_a_s = defs.get("service_path_aliases", {})
    if service in s_a_s:
        service = s_a_s[service]

    """
    Here we allow the addition of additional configuration files, necessary
    for options beyond basic library use. Files are read in from a `local`
    directory inside the script directory
        * this is the location of configuration file w/ content differing on
          the beaconServer instance
        * these files are inserted during installation (see the documentation)
    """
    if "services" in LOC_PATH or "byconaut" in LOC_PATH:
        scope = "services"
    else:
        scope = "beacon"
    
    byc.update({
        "request_path_root": scope,
        "request_entity_path_id": service
    })

    p_e_m = defs.get("path_entry_type_mappings", {})
    entry_type = p_e_m.get(service, "___none___")

    if entry_type in b_e_d:
        for d_k, d_v in b_e_d[entry_type].items():
            byc.update({d_k: d_v})

    # update response_entity_id from path
    update_entity_ids_from_path(byc)
    # update response_entity_id from form
    update_requested_schema_from_request(byc)
    set_response_entity(byc)
    set_response_schema(byc)
    set_special_modes(byc)
    select_dataset_ids(byc)
    set_user_name(byc)
    set_returned_granularities(byc)    
    parse_filters(byc)
    parse_variants(byc)


################################################################################

def set_special_modes(byc):
    if "test_mode" in BYC_PARS:
        BYC.update({"TEST_MODE": test_truthy(BYC_PARS["test_mode"])})
    if BYC.get("TEST_MODE") is True:
        BYC_PARS.update({"include_handovers": True})


################################################################################

def update_entity_ids_from_path(byc):
    req_p_id = byc.get("request_entity_path_id")
    s_a_s = BYC["beacon_defaults"].get("service_path_aliases", {})
    p_e_m = BYC["beacon_defaults"].get("path_entry_type_mappings", {})

    if not req_p_id:
        return
    res_p_id = byc.get("response_entity_path_id")
    if not res_p_id:
        res_p_id = req_p_id

    # TODO: in contrast to req_p_id, res_p_id hasn't been anti-aliased
    if res_p_id in s_a_s:
        res_p_id = s_a_s[res_p_id]

    # TODO: this gets the correct entity_id w/ entity_path_id fallback
    byc.update({
        "request_entity_id": p_e_m.get(req_p_id, req_p_id),
        "response_entity_id": p_e_m.get(res_p_id, req_p_id)
    })


################################################################################

def update_requested_schema_from_request(byc):
    # query_meta may come from the meta in a POST
    b_qm = byc.get("query_meta", {})

    # TODO: check if correct schema in request
    if "requested_schema" in BYC_PARS:
        byc.update({"response_entity_id": BYC_PARS.get("requested_schema", byc["response_entity_id"])})
    elif "requested_schemas" in b_qm:
        byc.update({"response_entity_id": b_qm["requested_schemas"][0].get("entity_type", byc["response_entity_id"])})


################################################################################

def set_response_entity(byc):
    prdbug(f'response_entity_id: {byc.get("response_entity_id")}')
    b_rt_s = BYC["beacon_defaults"].get("entity_defaults", {})
    r_e_id = byc.get("response_entity_id", "___none___")
    r_e = b_rt_s.get(r_e_id)
    if not r_e:
        return

    byc.update({"response_entity": r_e})


################################################################################

def set_response_schema(byc):
    r_e = byc.get("response_entity", {})
    r_s = r_e.get("response_schema", "beaconInfoResponse")
    byc.update({"response_schema": r_s})


