import inspect
import re
from deepmerge import always_merger
from os import environ, path

from config import *
from beacon_auth import *
from bycon_helpers import return_paginated_list, prdbug, prdbughead, RefactoredValues, set_debug_state, test_truthy
from dataset_parsing import select_dataset_ids


################################################################################

def set_beacon_defaults():
    defaults: object = BYC["beacon_defaults"].get("defaults", {})
    for d_k, d_v in defaults.items():
        BYC.update( { d_k: d_v } )  


################################################################################

def initialize_bycon_service():
    set_special_modes()
    select_dataset_ids()
    set_user_name()
    set_returned_granularities()    


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

    As approximation in a script one can override the original selection by providing
    a `--responseEntityPathId analyses` (or "individuals" etc.) parameter or forcing
    ```
    BYC_PARS.update({"response_entity_path_id":"analyses"})
    set_entities()
    ```
    """
    b_e_d = BYC.get("entity_defaults", {})
    arg_defs = BYC["argument_definitions"].get("$defs", {})

    # here aliases are read in, e.g. to allow "schemas" instead of "byconschemas"
    # ("schemas" is avoided since being "keywordy") etc.
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
    if (q_p_id := BYC_PARS.get("request_entity_path_id", "___none___")) in dealiased_path_ids.keys():
        BYC.update({"request_entity_path_id": q_p_id})
    if (p_p_id := BYC_PARS.get("response_entity_path_id", "___none___")) in dealiased_path_ids.keys():
        BYC.update({"response_entity_path_id": p_p_id})

    if (p_i_d := BYC.get("request_entity_path_id", "___none___")) not in dealiased_path_ids.keys():
        p_i_d = "info"
    
    if (rp_i_d := BYC.get("response_entity_path_id", "___none___")) not in dealiased_path_ids.keys():
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
        "request_entity_path_id": q_id,
        "response_entity_id": rp_d.get("response_entity_id", q_id),
        "response_entity_path_id": rp_i_d,
        "response_entity": rp_d,
        "response_schema": rp_d.get("response_schema", "beaconInfoResponse"),
        "bycon_response_class": rp_d.get("bycon_response_class", "BeaconInfoResponse")
    })

    if (rpidv := BYC.get("request_entity_path_id_value")):
        if p_p in arg_defs.keys():
            v = RefactoredValues(arg_defs[p_p]).refVal(rpidv)
            BYC_PARS.update({p_p: v})

