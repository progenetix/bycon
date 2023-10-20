import inspect
import re
from deepmerge import always_merger
from os import environ, path

from args_parsing import *
from bycon_helpers import return_paginated_list
from cgi_parsing import prdbug
from dataset_parsing import select_dataset_ids
from export_file_generation import *
from filter_parsing import parse_filters
from interval_utils import generate_genomic_mappings
from read_specs import read_service_prefs, update_rootpars_from_local
from response_remapping import callsets_create_iset
from variant_parsing import parse_variants

################################################################################

def set_byc_config_pars(byc):
    config = byc.get("config", {})
    b_r_p = config.get("byc_root_pars", {})
    for k, v in b_r_p.items():
        byc.update({k: v})

    config.pop("byc_root_pars", None)
    byc.update({"config": config})


################################################################################

def set_beacon_defaults(byc):

    b_d = byc.get("beacon_defaults", {})
    defaults: object = b_d.get("defaults", {})
    for d_k, d_v in defaults.items():
        byc.update( { d_k: d_v } )


################################################################################

def run_beacon_init_stack(byc):
    select_dataset_ids(byc)
    # # move the next to later, and deliver as Beacon error?
    # if len(byc["dataset_ids"]) < 1:
    #     print_text_response("No existing dataset_id - please check dataset_definitions")
    parse_filters(byc)
    parse_variants(byc)
    generate_genomic_mappings(byc)

################################################################################

def initialize_bycon_service(byc, service=False):
    """For consistency, the name of the local configuration file should usually
    correspond to the calling main function. However, an overwrite can be
    provided."""

    form = byc.get("form_data", {})
    scope = "beacon"

    if not service:
        service = byc.get("request_entity_path_id", False)
    frm = inspect.stack()[1]
    if not service:
        service = frm.function

    # TODO - streamline, also for services etc.
    s_a_s = byc["beacon_defaults"].get("service_path_aliases", {})

    if service in s_a_s:
        service = s_a_s[service]

    mod = inspect.getmodule(frm[0])

    if mod is not None:
        """
        Here we allow the addition of additional configuration files, necessary
        for options beyond basic library use. Files are read in as
        1. from a `local` directory inside the script directory
            * this is the location of configuration file w/ content differing on
              the beaconServer instance
            * these files are inserted during installation (see the documentation)
        2. from a `config` directory inside the script directory
            * script specific configurations are stored there under the name of
              script, e.g. `frequencymaps_creator.yaml` - typically only
              used in services and utility scripts, not beaconServer
            * this is usually used to provide script-specific parameters
              (`service_defaults`...)
        """
        pkg_path = path.dirname(path.abspath(mod.__file__))
        if "services" in pkg_path or "byconaut" in pkg_path:
            scope = "services"
        byc.update({
            "request_path_root": scope,
            "request_entity_path_id": service
        })

        loc_dir = path.join( pkg_path, "local" )
        conf_dir = path.join( pkg_path, "config" )
        
        # updates `beacon_defaults`, `dataset_definitions` and `local_paths`
        update_rootpars_from_local(loc_dir, byc)

        defaults = byc["beacon_defaults"].get("defaults", {})
        for d_k, d_v in defaults.items():
            byc.update({d_k: d_v})

        # this will generate byc["service_config"] if a file with the service
        # name exists
        read_service_prefs(service, conf_dir, byc)

    get_bycon_args(byc)
    args_update_form(byc)

    if "defaults" in byc.get("service_config", {}):
        for d_k, d_v in byc["service_config"]["defaults"].items():
            byc.update({d_k: d_v})

    defs = byc.get("beacon_defaults", {})
    b_e_d = defs.get("entity_defaults", {})

    p_e_m = byc["beacon_defaults"].get("path_entry_type_mappings", {})
    entry_type = p_e_m.get(service, "___none___")

    if entry_type in b_e_d:
        for d_k, d_v in b_e_d[entry_type].items():
            # prdbug(byc, {d_k: d_v})
            byc.update({d_k: d_v})

    # update response_entity_id from path
    update_entity_ids_from_path(byc)

    # update response_entity_id from form
    update_requested_schema_from_request(byc)
    set_response_entity(byc)
    set_response_schema(byc)

    set_io_params(byc)
    # CAVE: At this time the genome is just taken from the default so has to 
    # be run again after form value parsing ...
    generate_genomic_mappings(byc)
    set_special_modes(byc)

    # TODO: standardize the general defaults / entity defaults / form values merging
    #       through pre-parsing into identical structures and then use deepmerge etc.


################################################################################

def set_special_modes(byc):
    form = byc["form_data"]
    for m in ["test_mode", "debug_mode", "download_mode", "include_handovers"]:
        if m in form:
            v = test_truthy(form.get(m, False))
            byc.update({m: v})

    if byc.get("test_mode", False) is True:
        byc.update({"include_handovers": True})

    t_m_k = form.get("test_mode_count", "___none___")
    if re.match(r'^\d+$', str(t_m_k)):
        byc.update({"test_mode_count": int(t_m_k)})


################################################################################

def set_io_params(byc):
    form = byc["form_data"]

    if not "pagination" in byc:
        byc.update({"pagination": {"skip": 0, "limit": 0}})

    for sp in ["skip", "limit"]:
        if sp in form:
            if re.match(r'^\d+$', str(form[sp])):
                s_v = int(form[sp])
                byc["pagination"].update({sp: s_v})

    byc.update({"output": form.get("output", byc["output"])})
    byc.update({"method": form.get("method", byc["method"])})

    # TODO: this is only used in some services ...
    if "method_keys" in byc["service_config"]:
        m = form.get("method", "___none___")
        if m in byc["service_config"]["method_keys"].keys():
            byc["method"] = m


################################################################################

def update_entity_ids_from_path(byc):
    if not byc["request_entity_path_id"]:
        return

    if not byc["response_entity_path_id"]:
        byc.update({"response_entity_path_id": byc["request_entity_path_id"]})

    req_p_id = byc["request_entity_path_id"]
    res_p_id = byc["response_entity_path_id"]

    # TODO: in contrast to req_p_id, res_p_id hasn't been anti-aliased
    s_a_s = byc["beacon_defaults"].get("service_path_aliases", {})
    if res_p_id in s_a_s:
        res_p_id = s_a_s[res_p_id]

    p_e_m = byc["beacon_defaults"].get("path_entry_type_mappings", {})

    byc.update({
        "request_entity_id": p_e_m.get(req_p_id, req_p_id),
        "response_entity_id": p_e_m.get(res_p_id, res_p_id)
    })


################################################################################

def update_requested_schema_from_request(byc):
    form = byc["form_data"]
    b_qm = byc.get("query_meta", {})

    # TODO: check if correct schema in request
    if "requested_schema" in form:
        byc.update({"response_entity_id": form.get("requested_schema", byc["response_entity_id"])})
    elif "requested_schemas" in b_qm:
        byc.update({"response_entity_id": b_qm["requested_schemas"][0].get("entity_type", byc["response_entity_id"])})


################################################################################

def set_response_entity(byc):
    b_rt_s = byc["beacon_defaults"].get("entity_defaults", {})
    r_e_id = byc.get("response_entity_id", "___none___")
    r_e = b_rt_s.get(r_e_id)
    if not r_e:
        return

    byc.update({"response_entity": r_e})


################################################################################

def set_response_schema(byc):
    r_s = byc["response_entity"].get("response_schema", "beaconInfoResponse")
    byc.update({"response_schema": r_s})


################################################################################

def check_computed_interval_frequency_delivery(byc):
    if not "frequencies" in byc["output"]:
        return

    ds_id = byc["dataset_ids"][0]
    ds_results = byc["dataset_results"][ds_id]
    p_r = byc["pagination"]

    if not "callsets._id" in ds_results:
        return

    cs_r = ds_results["callsets._id"]

    mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
    cs_coll = mongo_client[ds_id]["callsets"]

    open_text_streaming(byc["env"], "interval_cnv_frequencies.pgxseg")

    for d in ["id", "assemblyId"]:
        print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    print_filters_meta_line(byc)
    print('#meta=>query="{}"'.format(json.dumps(byc["queries_at_execution"], indent=None, sort_keys=True, default=str)))
    print('#meta=>skip={};limit={}'.format(p_r["skip"], p_r["limit"]))
    print("#meta=>sample_no={}".format(cs_r["target_count"]))

    q_vals = cs_r["target_values"]
    r_no = len(q_vals)
    if r_no > p_r["limit"]:
        q_vals = return_paginated_list(q_vals, byc.get("skip", 0), byc.get("limit", 0))
        print(f'#meta=>"WARNING: Only {len(q_vals)} analyses (out of {r_no}) used for calculations due to pagination skip and limit"')

    h_ks = ["reference_name", "start", "end", "gain_frequency", "loss_frequency", "no"]
    print("group_id\t" + "\t".join(h_ks))

    cs_cursor = cs_coll.find({"_id": {"$in": q_vals}, "cnv_statusmaps": {"$exists":True}})

    intervals, cnv_cs_count = interval_counts_from_callsets(cs_cursor, byc)

    for intv in intervals:
        v_line = []
        v_line.append("query_result")
        for k in h_ks:
            v_line.append(str(intv[k]))
        print("\t".join(v_line))

    close_text_streaming()


################################################################################

def bycon_bundle_create_intervalfrequencies_object(bycon_bundle, byc):
    return callsets_create_iset("import", "", bycon_bundle["callsets"], byc)


################################################################################
