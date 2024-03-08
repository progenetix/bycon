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
    b_e_d = BYC.get("entity_defaults", {})
    p_e_m = BYC.get("path_entry_type_mappings", {})
    e_p_m = BYC.get("entry_type_path_mappings", {})
    if service in p_e_m.keys():
        e = p_e_m.get(service)
        service = e_p_m.get(e)
    entry_type = p_e_m.get(service, "___none___")

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
    if not (req_p_id := byc.get("request_entity_path_id")):
        return
    if not (res_p_id := byc.get("response_entity_path_id")):
        res_p_id = req_p_id

    # TODO: this gets the correct entity_id w/ entity_path_id fallback
    p_e_m = BYC.get("path_entry_type_mappings", {})
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
    byc.update({"response_entity": {}})
    b_rt_s = BYC.get("entity_defaults", {})
    r_e_id = byc.get("response_entity_id", "___none___")
    if (r_e := b_rt_s.get(r_e_id)):
        byc.update({"response_entity": r_e})


################################################################################

def set_response_schema(byc):
    r_e = byc.get("response_entity", {})
    r_s = r_e.get("response_schema", "beaconInfoResponse")
    byc.update({"response_schema": r_s})


