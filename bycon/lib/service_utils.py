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
    prdbug(f'initialize_bycon_service - ds_id: {BYC["BYC_DATASET_IDS"]}')
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
    d_p_e = BYC.get("data_pipeline_entities", [])

    # reating the maps for entity <-> path (or alias) mapping
    p_e_m = {}
    e_p_m = {}
    for e, e_d in b_e_d.items():
        if (p := e_d.get("request_entity_path_id")):
            p_e_m.update({ p: e })
            e_p_m.update({ e: p })
        for a in e_d.get("request_entity_path_aliases", []):
            p_e_m.update({ a: e })
        if "beaconResultsetsResponse" in e_d.get("response_schema", ""):
            d_p_e.append(e)

    # TODO - FIX to remove all the specials
    d_p_e = ['analysis', 'biosample', 'genomicVariant', 'individual', 'run']

    # override of path
    if (e_p_id := BYC_PARS.get("request_entity_path_id", "___none___")) in p_e_m:
        BYC.update({"request_entity_path_id": e_p_id})
    if (r_p_id := BYC_PARS.get("response_entity_path_id", "___none___")) in p_e_m:
        BYC.update({"response_entity_path_id": r_p_id})

    rq_p_id = BYC.get("request_entity_path_id", "info")
    rp_p_id = BYC.get("response_entity_path_id", rq_p_id)

    prdbug(f'... set_entities - request_entity_path_id: {rq_p_id}')
    prdbug(f'... set_entities - response_entity_path_id: {rp_p_id}')

    rq_id = p_e_m.get(rq_p_id)
    # again mapped to get the standard path for the entity in case the
    # original one was an alias (e.g. `service-info` for `info`)
    # rq_p_id = e_p_m.get(rq_id)

    # usually no different response entity
    if rp_p_id not in p_e_m:
        rp_p_id = e_p_m.get(rq_id)

    # there is a `requestedSchema` parameter (not `requestEntityId`)
    # in Beacon; so this is now used to provide the requested entity
    # if not, using the one from the response path item (which had a
    # fallback to the request path already)

    # TODO: breaks the services use ATM if a correct schema is added
    if (rp_id := BYC_PARS.get("requested_schema", "___none___")) not in e_p_m:
        rp_id = p_e_m.get(rp_p_id)

    # as above. in case of alias
    rp_p_id = e_p_m.get(rp_id)

    r_e = b_e_d.get(rp_id, {"response_schema": "beaconInfoResponse"})
    r_s = r_e.get("response_schema", "beaconInfoResponse")

    BYC.update({
        "data_pipeline_entities": d_p_e,
        "request_entity_id": rq_id,
        "request_entity_path_id": rq_p_id,
        "response_entity_id": rp_id,
        "response_entity_path_id": rp_p_id,
        "response_entity": r_e,
        "response_schema": r_s
    })

    # prdbug(f'"response_entity_id": {rp_id}; ')


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


