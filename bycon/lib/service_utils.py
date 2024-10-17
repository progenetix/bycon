import inspect
import re
from deepmerge import always_merger
from os import environ, path

from args_parsing import *
from config import *
from beacon_auth import *
from bycon_helpers import return_paginated_list, prdbug, prdbughead, set_debug_state, test_truthy
from dataset_parsing import select_dataset_ids
from parse_filters_request import parse_filters


################################################################################

def set_beacon_defaults():
    defaults: object = BYC["beacon_defaults"].get("defaults", {})
    for d_k, d_v in defaults.items():
        BYC.update( { d_k: d_v } )  


################################################################################

def initialize_bycon_service():
    update_requested_schema_from_request()
    set_special_modes()
    select_dataset_ids()
    set_user_name()
    set_returned_granularities()    
    parse_filters()


################################################################################

def set_special_modes():
    if "test_mode" in BYC_PARS:
        BYC.update({"TEST_MODE": test_truthy(BYC_PARS["test_mode"])})
    if BYC.get("TEST_MODE") is True:
        BYC_PARS.update({"include_handovers": True})


################################################################################

def set_entities():
    """
    This function evaluates the definitions for the entities and their selection
    by path elements (including aliases) or parameters and updates the global
    BYC definitions.
    """
    b_e_d = BYC.get("entity_defaults", {})

    dealiased_path_ids = {}
    for e, e_d in b_e_d.items():
        p_id = e_d.get("request_entity_path_id")
        dealiased_path_ids.update({p_id: e})
        for p_a_s in e_d.get("request_entity_path_aliases", []):
            dealiased_path_ids.update({p_a_s: e})

    # this allows to override the path values with parameters
    # it should only apply to special cases (e.g. overriding the standard
    # biosample table export in services with individuals) or for command
    # line testing
    if (e_p_id := BYC_PARS.get("request_entity_path_id", "___none___")) in dealiased_path_ids.keys():
        BYC.update({"request_entity_path_id": e_p_id})
    if (e_p_id := BYC_PARS.get("response_entity_path_id", "___none___")) in dealiased_path_ids.keys():
        BYC.update({"response_entity_path_id": e_p_id})

    p_i_d = BYC.get("request_entity_path_id", "___none___")
    if p_i_d not in dealiased_path_ids.keys():
        p_i_d = "info"
    rp_i_d = BYC.get("response_entity_path_id", "___none___")
    if rp_i_d not in dealiased_path_ids.keys():
        rp_i_d = p_i_d

    # after settling the paths we can get the entity ids
    q_id = dealiased_path_ids[p_i_d]
    r_id = dealiased_path_ids[rp_i_d]

    rq_d = b_e_d.get(q_id)
    rp_d = b_e_d.get(r_id)

    p_p = rq_d.get("path_id_value_bycon_parameter", "id")

    BYC.update({
        "path_id_value_bycon_parameter": p_p,
        "request_entity_id": rq_d.get("request_entity_id", q_id),
        "request_entity_path_id": p_i_d,
        "response_entity_id": rp_d.get("response_entity_id", q_id),
        "response_entity_path_id": rp_i_d,
        "response_entity": rp_d,
        "response_schema": rp_d.get("response_schema", "beaconInfoResponse"),
        "bycon_response_class": rp_d.get("bycon_response_class", "BeaconInfoResponse")
    })

    if (rpidv := BYC.get("request_entity_path_id_value")):
        BYC_PARS.update({p_p: rpidv})


################################################################################

def update_requested_schema_from_request():
    # query_meta may come from the meta in a POST
    b_qm = BYC.get("query_meta", {})

    # TODO: check if correct schema in request
    if "requested_schema" in BYC_PARS:
        BYC.update({"response_entity_id": BYC_PARS.get("requested_schema", BYC["response_entity_id"])})
    elif "requested_schemas" in b_qm:
        BYC.update({"response_entity_id": b_qm["requested_schemas"][0].get("entity_type", BYC["response_entity_id"])})


################################################################################

def set_response_schema():
    r_e = BYC.get("response_entity", {})
    r_s = r_e.get("response_schema", "beaconInfoResponse")
    BYC.update({"response_schema": r_s})

