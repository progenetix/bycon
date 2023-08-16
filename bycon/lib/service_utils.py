import inspect
from os import environ, path, pardir
from pathlib import Path

from args_parsing import *
from bycon_plot import ByconPlot
from bycon_helpers import paginate_list, set_pagination_range, mongo_result_list
from cgi_parsing import prjsonnice, prdbug
from data_retrieval import *
from dataset_parsing import select_dataset_ids
from datatable_utils import export_datatable_download
from deepmerge import always_merger
from export_file_generation import *
from file_utils import ByconBundler, callset_guess_probefile_path
from filter_parsing import parse_filters
from handover_generation import dataset_response_add_handovers, query_results_save_handovers, \
    dataset_results_save_handovers
from interval_utils import generate_genomic_mappings
from query_execution import execute_bycon_queries
from read_specs import read_bycon_definition_files, read_service_prefs
from response_remapping import *
from variant_mapping import ByconVariant
from variant_parsing import parse_variants
from schema_parsing import object_instance_from_schema_name

################################################################################

def initialize_bycon(config):

    b_r_p = config.get("byc_root_pars", {})

    bycon_lib_path = path.dirname(path.abspath(__file__))
    pkg_path = path.join(bycon_lib_path, pardir)

    byc = {
        "pkg_path": pkg_path,
        "bycon_lib_path": bycon_lib_path
    }

    for k, v in b_r_p.items():
        byc.update({k: v})

    config.pop("byc_root_pars", None)
    byc.update({"config": config})

    if not environ.get('HTTP_HOST'):
        byc.update({"env": "local"})

    return byc


################################################################################

def beacon_data_pipeline(byc, entry_type):
    initialize_bycon_service(byc, entry_type)

    run_beacon_init_stack(byc)
    return_filtering_terms_response(byc)
    run_result_sets_beacon(byc)
    update_meta_queries(byc)
    query_results_save_handovers(byc)
    check_callset_plot_delivery(byc)
    check_biosamples_map_delivery(byc)
    check_computed_histoplot_delivery(byc)
    check_computed_interval_frequency_delivery(byc)
    check_switch_to_count_response(byc)
    check_switch_to_boolean_response(byc)
    cgi_print_response(byc, 200)


################################################################################

def run_beacon_init_stack(byc):
    select_dataset_ids(byc)
    if len(byc["dataset_ids"]) < 1:
        print_text_response("No existing dataset_id - please check dataset_definitions")

    create_empty_beacon_response(byc)
    parse_filters(byc)
    parse_variants(byc)
    response_add_received_request_summary_parameters(byc)
    generate_genomic_mappings(byc)

    cgi_break_on_errors(byc)


################################################################################

def initialize_bycon_service(byc, service=False):
    """For consistency, the name of the local configuration file should usually
    correspond to the calling main function. However, an overwrite can be
    provided."""

    form = byc["form_data"]
    scope = "beacon"

    if not service:
        service = byc.get("request_entity_path_id", False)
    frm = inspect.stack()[1]
    if not service:
        service = frm.function

    # TODO - streamline, also for services etc.
    s_a_s = byc["beacon_mappings"].get("service_aliases", {})

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
        service_path = path.dirname(path.abspath(mod.__file__))
        if "services" in service_path or "byconaut" in service_path:
            scope = "services"
        byc.update({
            "request_path_root": scope,
            "request_entity_path_id": service
        })

        l_pref_dir = path.join(service_path, "local")

        read_bycon_definition_files(l_pref_dir, byc)
        b_m = byc.get("beacon_mappings", {})
        s_m = byc.get("services_mappings", {})
        byc.update({"beacon_mappings": always_merger.merge(s_m, b_m)})
        b_s = byc.get("beacon_defaults", {})
        s_s = byc.get("services_defaults", {})
        byc.update({"beacon_defaults": always_merger.merge(s_s, b_s)})
        defaults = byc["beacon_defaults"].get("defaults", {})
        for d_k, d_v in defaults.items():
            byc.update({d_k: d_v})

        # this will generate byc["service_config"] if a file with the service
        # name exists
        s_pref_dir = path.join(service_path, "config")
        read_service_prefs(service, s_pref_dir, byc)

    get_bycon_args(byc)
    args_update_form(byc)

    if "defaults" in byc.get("service_config", {}):
        for d_k, d_v in byc["service_config"]["defaults"].items():
            byc.update({d_k: d_v})

    defs = byc.get("beacon_defaults", {})
    b_e_d = defs.get("entity_defaults", {})

    p_e_m = byc["beacon_mappings"].get("path_entry_type_mappings", {})
    entry_type = p_e_m.get(service, "___none___")

    if entry_type in b_e_d:
        for d_k, d_v in b_e_d[entry_type].items():
            byc.update({d_k: d_v})

    # update response_entity_id from path
    update_entity_ids_from_path(byc)

    # update response_entity_id from form
    update_requested_schema_from_request(byc)
    set_response_entity(byc)

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

    p_r_m = byc["beacon_mappings"].get("path_entry_type_mappings", {})

    byc.update({
        "request_entity_id": p_r_m.get(req_p_id, byc["request_entity_path_id"]),
        "response_entity_id": p_r_m.get(res_p_id, byc["response_entity_path_id"])
    })


################################################################################

def update_requested_schema_from_request(byc):
    b_mps = byc["beacon_mappings"]
    form = byc["form_data"]
    b_qm = byc["query_meta"]

    if "requested_schema" in form:
        byc.update({"response_entity_id": form.get("requested_schema", byc["response_entity_id"])})
    elif "requested_schemas" in b_qm:
        byc.update({"response_entity_id": b_qm["requested_schemas"][0].get("entity_type", byc["response_entity_id"])})


################################################################################

def set_response_entity(byc):
    b_rt_s = byc["beacon_defaults"].get("entity_defaults", {})
    r_e_id = byc.get("response_entity_id", "___none___")

    if r_e_id not in b_rt_s.keys():
        return

    byc.update({"response_entity": b_rt_s.get(r_e_id)})


################################################################################

def run_result_sets_beacon(byc):
    sr_r = byc["service_response"]["response"]

    byc.update({"dataset_results": {}})

    ######## result sets loop ##################################################

    for i, r_set in enumerate(sr_r["result_sets"]):

        ds_id = r_set["id"]

        r_set, r_s_res = populate_result_set(r_set, byc)

        if r_set["results_count"] < 1:
            continue

        # TODO: This condition avoids the "range on range" if previously set for
        # a handover query (by accessioinId)
        if not "range" in byc["pagination"]:
            set_pagination_range(len(r_s_res), byc)
        if test_truthy(byc["form_data"].get("paginate_results", True)):
            r_s_res = paginate_list(r_s_res, byc)

        check_alternative_single_set_deliveries(ds_id, r_s_res, byc)
        r_s_res = reshape_resultset_results(ds_id, r_s_res, byc)

        sr_r["result_sets"][i].update({
            "paginated_results_count": len(r_s_res),
            "exists": True,
            "results": r_s_res
        })

    ######## end of result sets loop ###########################################

    sr_rs = byc["service_response"].get("response_summary", {})
    sr_rs.update({"num_total_results": 0})
    for r_set in sr_r["result_sets"]:
        sr_rs["num_total_results"] += r_set["results_count"]

    if sr_rs["num_total_results"] > 0:
        sr_rs.update({"exists": True})


################################################################################

def populate_result_set(r_set, byc):
    ds_id = r_set["id"]
    execute_bycon_queries(ds_id, byc)

    # # Special check-out here since this forces a single handover
    # check_plot_responses(ds_id, byc)

    r_set.update({"results_handovers": dataset_response_add_handovers(ds_id, byc)})
    r_s_res = retrieve_data(ds_id, byc)

    r_set_update_counts(r_set, r_s_res, byc)

    return r_set, r_s_res


################################################################################

def r_set_update_counts(r_set, r_s_res, byc):
    ds_id = r_set["id"]
    ds_res = byc["dataset_results"][ds_id]

    r_set.update({"results_count": 0})
    counted = byc["config"].get("beacon_count_items", {})

    for c, c_d in counted.items():
        h_o_k = c_d.get("h->o_key", None)
        if h_o_k is None:
            continue
        if h_o_k not in ds_res:
            continue
        r_c = ds_res[h_o_k]["target_count"]
        s_c = len(list(set(ds_res[h_o_k]["target_values"])))
        r_set["info"]["counts"].update({c: r_c})

    if byc["empty_query_all_count"]:
        r_set.update({"results_count": byc["empty_query_all_count"]})
    elif isinstance(r_s_res, list):
        r_set.update({"results_count": len(r_s_res)})

    return r_set


################################################################################

def check_alternative_single_set_deliveries(ds_id, r_s_res, byc):
    check_datatable_delivery(r_s_res, byc)
    check_alternative_variant_deliveries(ds_id, byc)
    check_alternative_callset_deliveries(ds_id, byc)

    return


################################################################################

def response_meta_add_request_summary(r, byc):
    if not "received_request_summary" in r["meta"]:
        return r

    r_rcvd_rs = r["meta"]["received_request_summary"]
    defs = byc.get("beacon_defaults", {})

    api_v = "v2"
    try:
        api_v = defs["entity_defaults"]["info"].get("api_version", "v2")
    except:
        pass

    b_e_d = defs.get("entity_defaults", {"info":{}})

    form = byc["form_data"]

    r_rcvd_rs.update({
        "filters": byc.get("filters", []),
        "pagination": byc.get("pagination", {}),
        "api_version": api_v
    })

    for p in ["include_resultset_responses", "requested_granularity"]:
        if p in form:
            r_rcvd_rs.update({p: form.get(p)})
            if "requested_granularity" in p:
                r["meta"].update({"returned_granularity": form.get(p)})

    try:
        for rrs_k, rrs_v in byc["service_config"]["meta"]["received_request_summary"].items():
            r_rcvd_rs.update({rrs_k: rrs_v})
    except:
        pass

    if "queries_at_execution" in byc:
        if "info" in r["meta"]:
            r["meta"]["info"].update({"queries_at_execution": byc["queries_at_execution"]})
        else:
            r["meta"].update({"info": {"queries_at_execution": byc["queries_at_execution"]}})


    return r


################################################################################

def update_meta_queries(byc):
    try:
        if not "info" in byc["meta"]:
            byc["meta"].update({"info": {}})
        byc["service_response"]["meta"]["info"].update({"processed_query": byc.get("original_queries", {})})
    except:
        pass


################################################################################

def create_empty_beacon_response(byc):
    r_s = byc["response_entity"].get("response_schema", None)
    # prdbug(byc, f'{byc["response_entity"]} - {r_s}')
    if r_s is None:
        return

    r, e = instantiate_response_and_error(byc, r_s)
    # prjsonnice(r_s)

    try:
        r["response"].update({"result_sets": []})
    except KeyError:
        pass

    if "beaconResultsetsResponse" in r_s:

        # TODO: stringent definition on when this is being used
        r_set = object_instance_from_schema_name(byc, "beaconResultsets", "definitions/ResultsetInstance")

        if "dataset_ids" in byc:
            for ds_id in byc["dataset_ids"]:
                ds_rset = r_set.copy()
                ds_rset.update({
                    "id": ds_id,
                    "set_type": "dataset",
                    "results_count": 0,
                    "exists": False,
                    "info": {"counts": {}}
                })
                r["response"]["result_sets"].append(ds_rset)

    byc.update({"service_response": r, "error_response": e})


################################################################################

def create_empty_service_response(byc):
    r, e = instantiate_response_and_error(byc, byc["response_entity"]["response_schema"])
    byc.update({"service_response": r, "error_response": e})


###############################################################################

def create_empty_non_data_response(byc):
    r, e = instantiate_response_and_error(byc, byc["response_entity"]["response_schema"])
    response_update_meta(r, byc)

    for r_k, r_v in byc["service_config"]["response"].items():
        r["response"].update({r_k: r_v})

    byc.update({"service_response": r, "error_response": e})


################################################################################

def check_plot_responses(ds_id, byc):
    if not "plot" in byc["output"]:
        return

    check_histoplot_plot_response(ds_id, byc)


################################################################################

def check_histoplot_plot_response(ds_id, byc):
    h_o_types = byc["handover_definitions"]["h->o_types"]
    ds_h_o = byc["dataset_definitions"][ds_id].get("handoverTypes", h_o_types.keys())

    if "histoplot" not in ds_h_o:
        return

    byc["include_handovers"] = True
    byc["dataset_definitions"][ds_id].update({"handoverTypes": ["histoplot"]})
    dataset_results_save_handovers(ds_id, byc)
    r_s_ho = dataset_response_add_handovers(ds_id, byc)

    for h_o in r_s_ho:
        if "histoplot" in h_o["handover_type"]["id"]:
            print_uri_rewrite_response(h_o["url"], "")
            exit()


################################################################################

def check_datatable_delivery(results, byc):
    if not "table" in byc["output"]:
        return
    if not "datatable_mappings" in byc:
        return

    export_datatable_download(results, byc)


################################################################################

def instantiate_response_and_error(byc, schema):
    """The response relies on the pre-processing of input parameters (queries etc)."""
    r = object_instance_from_schema_name(byc, schema, "")
    m = object_instance_from_schema_name(byc, "beaconResponseMeta", "")
    r.update({"meta": m})
    e = object_instance_from_schema_name(byc, "beaconErrorResponse", "")
    response_update_meta(r, byc)
    error_response_set_defaults(e)

    return r, e


################################################################################

def response_update_meta(r, byc):
    if "response_summary" in r:
        r_s = r.get("response_summary")
        if r_s is None:
            r_s = {"exists": False}
        else:
            r_s.update({"exists": False})
        r.update({"response_summary": r_s})
    response_meta_set_info_defaults(r, byc)
    response_meta_set_config_defaults(r, byc)
    response_meta_set_entity_values(r, byc)
    response_meta_add_request_summary(r, byc)
    r["meta"].update({"test_mode": byc.get("test_mode", False)})


################################################################################

def error_response_set_defaults(e):
    e.update({
        "error" : {
            "error_code": 200,
            "error_message": ""
        }
    })


################################################################################

def response_meta_set_info_defaults(r, byc):
    defs = byc.get("beacon_defaults", {})
    b_e_d = defs.get("entity_defaults", {"info":{}})

    # TODO: command line hack ...
    for i_k in ["api_version", "beacon_id"]:
        if "meta" in r and "info" in b_e_d:
            r["meta"].update({i_k: b_e_d["info"].get(i_k, "")})


################################################################################

def response_meta_set_config_defaults(r, byc):
    # TODO: should be in schemas
    m = byc["service_config"].get("meta", {})
    for k, v in m.items():
        r["meta"].update({k: v})


################################################################################

def response_meta_set_entity_values(r, byc):
    try:
        r["meta"]["received_request_summary"].update({
            "requested_schemas": [byc["response_entity"]["beacon_schema"]]
        })
        r["meta"].update({"returned_schemas": [byc["response_entity"]["beacon_schema"]]})
    except:
        pass


################################################################################

def response_add_received_request_summary_parameters(byc):
    if not "received_request_summary" in byc["service_response"].get("meta", {}):
        return

    for name in ["method", "dataset_ids", "filters", "varguments", "test_mode"]:
        value = byc.get(name, False)
        if value is False:
            continue
        if "varguments" in name:
            name = "request_parameters"
        byc["service_response"]["meta"]["received_request_summary"].update({name: value})

################################################################################

def received_request_summary_add_custom_parameter(byc, parameter, value):
    try:
        byc["service_response"]["meta"]["received_request_summary"]["request_parameters"].update({parameter: value})
    except:
        pass

################################################################################

def response_add_error(byc, code=200, message=False):
    if message is False:
        return
    if len(str(message)) < 1:
        return

    e = {"error_code": code, "error_message": message}
    byc["error_response"].update({"error": e})


################################################################################

def response_add_warnings(byc, message=False):
    if message is False:
        return
    if len(str(message)) < 1:
        return

    if not "service_response" in byc:
        return

    if not "info" in byc["service_response"]:
        byc["service_response"].update({"info": {}})
    if not "warnings" in byc["service_response"]:
        byc["service_response"]["info"].update({"warnings": []})

    byc["service_response"]["info"]["warnings"].append(message)


################################################################################

def collations_set_delivery_keys(byc):
    # the method keys can be overriden with "deliveryKeys"

    method = byc.get("method", False)
    conf = byc["service_config"]

    d_k = form_return_listvalue(byc["form_data"], "deliveryKeys")

    if len(d_k) > 0:
        return d_k

    if method is False:
        return d_k

    # here the empty list is returned, leading to all
    if "details" in method:
        return d_k

    if not "method_keys" in conf:
        return d_k

    if method in conf["method_keys"]:
        d_k = conf["method_keys"][method]

    return d_k


################################################################################

def populate_service_response(byc, results):
    byc["service_response"].update({
        "response_summary": {
            "exists": False,
            "num_total_results": 0
        }
    })

    populate_service_header(byc, results)
    populate_service_response_counts(byc)

    if len(results) > 0:
        byc["service_response"]["response_summary"].update({
            "exists": True,
            "num_total_results": len(results)
        })

    if byc["service_response"]["response"] is None:
        byc["service_response"].update({"response": {"results":results}})
    else:
        byc["service_response"]["response"].update({"results": results})

    check_switch_to_count_response(byc)
    check_switch_to_boolean_response(byc)


################################################################################

def populate_service_header(byc, results):
    try:
        r_s = byc["service_response"]["response_summary"]
    except:
        return

    r_no = 0

    if isinstance(results, list):
        r_no = len(results)
        r_s.update({"num_total_results": r_no})
    if r_no > 0:
        r_s.update({"exists": True})


################################################################################

def populate_service_response_counts(byc):
    if not "dataset_results" in byc:
        return
    if not "dataset_ids" in byc:
        return

    ds_id = byc["dataset_ids"][0]

    if not ds_id in byc["dataset_results"]:
        return

    counts = {}
    counted = byc["config"].get("beacon_count_items", {})

    for c, c_d in counted.items():
        h_o_k = c_d.get("h->o_key")
        if not h_o_k:
            continue
        if h_o_k in byc["dataset_results"][ds_id]:
            counts[c] = byc["dataset_results"][ds_id][h_o_k]["target_count"]

    byc["service_response"]["info"].update({"counts": counts})


################################################################################

def check_alternative_variant_deliveries(ds_id, byc):
    if not "genomicVariant" in byc["response_entity_id"]:
        return

    export_pgxseg_download(ds_id, byc)
    export_vcf_download(ds_id, byc)
    export_variants_download(ds_id, byc)


################################################################################

def check_alternative_callset_deliveries(ds_id, byc):
    check_callsets_matrix_delivery(ds_id, byc)


################################################################################

def return_filtering_terms_response(byc):
    if not "filteringTerm" in byc["response_entity_id"]:
        return

    # TODO: correct response w/o need to fix
    # TODO: dataset specificity etc.
    byc["service_response"].update({"response": {"filteringTerms": [], "resources": []}})

    f_r_d = {}

    f_coll = byc["config"]["filtering_terms_coll"]

    f_t_s = []
    ft_fs = []

    if "filters" in byc:
        if len(byc["filters"]) > 0:
            for f in byc["filters"]:
                ft_fs.append('(' + f["id"] + ')')
    f_s = '|'.join(ft_fs)
    f_re = re.compile(r'^' + f_s)

    collation_types = set()

    scopes = ["biosamples", "individuals", "analyses", "genomicVariations"]

    for ds_id in byc["dataset_ids"]:

        query = {}

        try:
            if len(byc["form_data"]["scope"]) > 4:
                query.update({"scope": byc["form_data"]["scope"]})
        except:
            pass

        fields = {"_id": 0}

        f_s, e = mongo_result_list(ds_id, f_coll, query, fields)

        t_f_t_s = []

        for f in f_s:
            collation_types.add(f.get("collation_type", None))
            f_t = {"count": f.get("count", 0)}
            for k in ["id", "type", "label"]:
                if k in f:
                    f_t.update({k: f[k]})
            f_t.update({"scopes": scopes})
            t_f_t_s.append(f_t)

        f_t_s.extend(t_f_t_s)

    byc["service_response"]["response"].update({"filteringTerms": f_t_s})
    byc["service_response"]["response"].update({"resources": create_filters_resource_response(collation_types, byc)})
    byc["service_response"]["response_summary"].update({"num_total_results": len(f_t_s)})
    if len(f_t_s) > 0:
        byc["service_response"]["response_summary"].update({"exists": True})

    cgi_print_response(byc, 200)


################################################################################

def create_filters_resource_response(collation_types, byc):
    r_o = {}
    resources = []

    f_d_s = byc["filter_definitions"]
    collation_types = list(collation_types)
    res_schema = object_instance_from_schema_name(byc, "beaconFilteringTermsResults", "definitions/Resource",
                                                  "json")
    for c_t in collation_types:
        f_d = f_d_s[c_t]
        r = {}
        for k in res_schema.keys():
            if k in f_d:
                r.update({k: f_d[k]})

        r_o.update({f_d["namespace_prefix"]: r})

    for k, v in r_o.items():
        resources.append(v)
    return resources


################################################################################

def check_biosamples_map_delivery(byc):
    """
    TODO
    """


    return

################################################################################

def check_callset_plot_delivery(byc):
    if not "samplesplot" in byc["output"]:
        return

    results = []
    p_r = byc["pagination"]

    for ds_id in byc["dataset_results"].keys():

        ds_results = byc["dataset_results"][ds_id]
        if not "callsets._id" in ds_results:
            continue

        v_d = byc["variant_parameters"]
        mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
        cs_coll = mongo_client[ds_id]["callsets"]
        var_coll = mongo_client[ds_id]["variants"]

        cs_r = ds_results["callsets._id"]
        if len(cs_r) < 1:
            continue

        q_vals = cs_r["target_values"]
        r_no = len(q_vals)
        if r_no > p_r["limit"]:
            q_vals = paginate_list(q_vals, byc)

        for cs in cs_coll.find({"_id": {"$in": q_vals}}):

            cs_id = cs.get("id", "NA")

            cnv_chro_stats = cs.get("cnv_chro_stats", False)
            cnv_statusmaps = cs.get("cnv_statusmaps", False)

            if cnv_chro_stats is False or cnv_statusmaps is False:
                continue

            p_o = {
                "dataset_id": ds_id,
                "callset_id": cs_id,
                "biosample_id": cs.get("biosample_id", "NA"),
                "cnv_chro_stats": cs.get("cnv_chro_stats", {}),
                "cnv_statusmaps": cs.get("cnv_statusmaps", {}),
                "probefile": callset_guess_probefile_path(cs, byc),
                "variants": []
            }

            if r_no == 1 and p_o["probefile"] is not False:
                p_o.update({"cn_probes": ByconBundler(byc).read_probedata_file(p_o["probefile"]) })

            v_q = {"callset_id": cs_id}

            for v in var_coll.find(v_q):
                p_o["variants"].append(ByconVariant(byc).byconVariant(v))

            results.append(p_o)

    plot_data_bundle = {"callsets_variants_bundles": results}
    ByconPlot(byc, plot_data_bundle).svg_response()


################################################################################

def check_computed_histoplot_delivery(byc):
    if not "histo" in byc.get("output", "___none___"):
        return

    f_d = byc.get("filter_definitions", {})

    p_r = byc["pagination"]
    interval_sets = []

    for ds_id in byc["dataset_results"].keys():

        ds_results = byc["dataset_results"][ds_id]

        if not "callsets._id" in ds_results:
            continue

        mongo_client = MongoClient(host=environ.get("BYCON_MONGO_HOST", "localhost"))
        bios_coll = mongo_client[ds_id]["biosamples"]
        cs_coll = mongo_client[ds_id]["callsets"]

        f_s_dists = []
        f_s_k = ""
        f_s_t = byc["form_data"].get("plot_group_by", "___none___")

        if f_s_t in f_d.keys():

            if not "biosamples._id" in ds_results:
                continue

            bios_q_v = ds_results["biosamples._id"].get("target_values", [])
            if len(bios_q_v) < 1:
                continue

            f_s_k = f_d[f_s_t].get("db_key", "___none___")
            f_s_p = f_d[f_s_t].get("pattern", False)
            f_s_q = {"_id": {"$in": bios_q_v}}
            f_s_dists = bios_coll.distinct(f_s_k, f_s_q)
            if f_s_p is not False:
                r = re.compile(f_s_p)
                f_s_dists = list(filter(lambda d: r.match(d), f_s_dists))

            for f_s_id in f_s_dists:

                bios_id_q = {"$and": [
                    {f_s_k: f_s_id},
                    {"_id": {"$in": bios_q_v}}
                ]}

                bios_ids = bios_coll.distinct("id", bios_id_q)
                cs__ids = cs_coll.distinct("_id", {"biosample_id": {"$in": bios_ids}})
                r_no = len(cs__ids)
                if r_no > p_r["limit"]:
                    cs__ids = paginate_list(cs__ids, byc)

                label = f"Search Results (subset {f_s_id})"

                iset = callset__ids_create_iset(ds_id, label, cs__ids, byc)
                interval_sets.append(iset)

        else:
            cs_r = ds_results["callsets._id"]
            cs__ids = cs_r["target_values"]
            r_no = len(cs__ids)
            # filter for CNV cs before evaluating number
            if r_no > p_r["limit"]:
                cs_cnv_ids = []
                for _id in cs__ids:
                    cs = cs_coll.find_one({"_id":_id})
                    if "cnv_statusmaps" in cs:
                        cs_cnv_ids.append(_id)
                cs__ids = cs_cnv_ids
            cs__ids = paginate_list(cs__ids, byc)

            iset = callset__ids_create_iset(ds_id, "Search Results", cs__ids, byc)
            interval_sets.append(iset)

    plot_data_bundle = {"interval_frequencies_bundles": interval_sets}
    ByconPlot(byc, plot_data_bundle).svg_response()


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
        q_vals = paginate_list(q_vals, byc)
        print(
            '#meta=>"WARNING: Only analyses {} - {} (out of {}) used for calculations due to pagination skip and limit"'.format(
                (p_r["range"][0] + 1), p_r["range"][-1], cs_r["target_count"]))

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

def check_callsets_matrix_delivery(ds_id, byc):
    if not "pgxmatrix" in byc["output"]:
        return

    export_callsets_matrix(ds_id, byc)


################################################################################

def bycon_bundle_create_intervalfrequencies_object(bycon_bundle, byc):
    return callsets_create_iset("import", "", bycon_bundle["callsets"], byc)

################################################################################
