from os import environ, path, pardir
import inspect, json, random
from pathlib import Path
from pymongo import MongoClient
from bson import json_util

# local
bycon_lib_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( bycon_lib_path, pardir )

from args_parsing import *
from cgi_parsing import *
from cytoband_utils import translate_reference_ids
from data_retrieval import *
from datatable_utils import export_datatable_download
from export_file_generation import *
from handover_generation import dataset_response_add_handovers, query_results_save_handovers, dataset_results_save_handovers
from interval_utils import generate_genomic_intervals, interval_counts_from_callsets
from query_execution import execute_bycon_queries, process_empty_request, mongo_result_list
from query_generation import  initialize_beacon_queries, paginate_list, replace_queries_in_test_mode, set_pagination_range
from read_specs import load_yaml_empty_fallback, read_bycon_configs_by_name, read_bycon_definition_files, read_local_prefs
from response_remapping import *
from schema_parsing import *

################################################################################

def initialize_bycon(config):

    b_r_p = config.get("byc_root_pars", {})

    byc =  {
        "pkg_path": pkg_path,
        "bycon_lib_path": bycon_lib_path
    }

    for k, v in b_r_p.items():
        byc.update({k:v})

    config.pop("byc_root_pars", None)
    byc.update({"config":config})

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
    check_computed_interval_frequency_delivery(byc)
    check_switch_to_count_response(byc)
    check_switch_to_boolean_response(byc)
    cgi_print_response( byc, 200 )

################################################################################

def initialize_bycon_service(byc, service=False):

    """For consistency, the name of the local configuration file should usually
    correspond to the calling main function. However, an overwrite can be
    provided."""

    defs = byc.get("beacon_defaults", {})
    b_e_d = defs.get("entity_defaults", {})    
    form = byc["form_data"]

    frm = inspect.stack()[1]
    if service is False:
        service = frm.function

    # TODO - streamline
    s_a_s = byc["beacon_mappings"].get("service_aliases", {})

    if service in s_a_s:
        service = s_a_s[service]

    mod = inspect.getmodule(frm[0])
    if mod is not None:
        """
        Here we allow the addition of additional configuration files, necessary
        for options beyond basic library use. Files are read in as
        1. from a `config` directory in the parent directory of the executed script
            * this e.g. overwrites the config options
        2. from a config directory inside the script directory
            * this is usually used to provide script-specific parameters (`service_defaults`...)
        """
        sub_path = path.dirname( path.abspath(mod.__file__) )
        conf_dir = path.join( sub_path, "local" )
        if path.isdir(conf_dir):
            c_f = Path( path.join( conf_dir, "config.yaml" ) )
            if path.isfile(c_f):
                byc.update({"config": load_yaml_empty_fallback( c_f ) })
            d_f = Path( path.join( conf_dir, "beacon_defaults.yaml" ) )
            if path.isfile(d_f):
                byc.update({"beacon_defaults": load_yaml_empty_fallback( d_f ) })
                defaults = byc["beacon_defaults"].get("defaults", {})
                for d_k, d_v in defaults.items():
                    byc.update( { d_k: d_v } )
            read_bycon_definition_files(conf_dir, byc)

        read_local_prefs( service, sub_path, byc )

    get_bycon_args(byc)
    args_update_form(byc)

    conf = byc["service_config"]

    if "defaults" in conf:
        for d_k, d_v in conf["defaults"].items():
            byc.update( { d_k: d_v } )

    if service in b_e_d:
        for d_k, d_v in b_e_d[ service ].items():
            byc.update( { d_k: d_v } )

    # update response_entity_id from path
    update_entity_ids_from_path(byc)
    # update response_entity_id from form
    update_requested_schema_from_request(byc)
    set_response_entity(byc)

    set_io_params(byc)
    translate_reference_ids(byc)
    set_special_modes(byc)

    # TODO: standardize the general defaults / entity defaults / form values merging
    #       through pre-parsing into identical structures and then use deepmerge etc.

    return byc

################################################################################

def set_special_modes(byc):

    form = byc["form_data"]
    for m in ["test_mode", "debug_mode", "download_mode", "include_handovers"]:
        if m in form:
            byc.update({m: test_truthy( form.get(m, False) ) })

    t_m_k = form.get("test_mode_count", "___none___")
    if re.match(r'^\d+$', str(t_m_k)):
        byc.update({"test_mode_count": int(t_m_k) })

    return byc

################################################################################

def set_io_params(byc):

    form = byc["form_data"]

    if not "pagination" in byc:
        byc.update( { "pagination": {"skip": 0, "limit": 0 } } )

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

    return byc

################################################################################

def update_entity_ids_from_path(byc):

    if not byc["request_entity_path_id"]:
        return byc

    if not byc["response_entity_path_id"]:
        byc.update({ "response_entity_path_id": byc["request_entity_path_id"] })

    req_p_id = byc["request_entity_path_id"]
    res_p_id = byc["response_entity_path_id"]

    m_k = byc["request_path_root"] + "_mappings"
    b_mps = byc[m_k]
    p_r_m = b_mps["path_response_type_mappings"]

    byc.update({
        "request_entity_id": p_r_m.get(req_p_id, byc["request_entity_path_id"]),
        "response_entity_id": p_r_m.get(res_p_id, byc["response_entity_path_id"])
    })


    return byc

################################################################################

def update_requested_schema_from_request(byc):

    m_k = byc["request_path_root"] + "_mappings"
    b_mps = byc[m_k]
    form = byc["form_data"]
    b_qm = byc["query_meta"]

    if "requested_schema" in form:
        byc.update({"response_entity_id": form.get("requested_schema", byc["response_entity_id"])})
    elif "requested_schemas" in b_qm:
        byc.update({"response_entity_id": b_qm["requested_schemas"][0].get("entity_type", byc["response_entity_id"])})

    return byc

################################################################################

def set_response_entity(byc):

    m_k = byc["request_path_root"] + "_mappings"
    b_rt_s = byc[m_k]["response_types"]

    if byc["response_entity_id"] in b_rt_s.keys():
        byc.update({"response_entity": b_rt_s[ byc["response_entity_id"] ] })

    return byc

################################################################################

def run_beacon_init_stack(byc):

    initialize_beacon_queries(byc)
    generate_genomic_intervals(byc)
    create_empty_beacon_response(byc)
    replace_queries_in_test_mode(byc)
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    return byc

################################################################################

def run_result_sets_beacon(byc):

    sr_r = byc["service_response"]["response"]

    byc.update({"dataset_results":{}})

    ######## result sets loop ##################################################

    for i, r_set in enumerate(sr_r["result_sets"]):

        ds_id = r_set["id"]

        execute_bycon_queries( ds_id, byc )

        # Special check-out here since this forces a single handover
        check_plot_responses(ds_id, byc)

        r_set.update({ "results_handovers": dataset_response_add_handovers(ds_id, byc) })
        r_s_res = retrieve_data(ds_id, byc)

        r_set_update_counts(r_set, r_s_res, byc)
        if r_set["results_count"] < 1:
            continue

        # TODO: This condition avoids the "range on range" if previously set for a handover
        # query (by accessioinId)
        if not "range" in byc["pagination"]:
            set_pagination_range(len(r_s_res), byc)
        
        if test_truthy( byc["form_data"].get("paginate_results", True) ):
            r_s_res = paginate_list(r_s_res, byc)

        check_alternative_single_set_deliveries(ds_id, r_s_res, byc)
        r_s_res = reshape_resultset_results(ds_id, r_s_res, byc)

        sr_r["result_sets"][i].update({
            "paginated_results_count": len( r_s_res ),
            "exists": True,
            "results": r_s_res
        })

    ######## end of result sets loop ###########################################

    sr_rs = byc["service_response"].get("response_summary", {})
    sr_rs.update({"num_total_results":0})
    for r_set in sr_r["result_sets"]:
        sr_rs["num_total_results"] += r_set["results_count"]

    if sr_rs["num_total_results"] > 0:
        sr_rs.update({"exists": True })

    return byc

################################################################################

def r_set_update_counts(r_set, r_s_res, byc):

    ds_id = r_set["id"]


    r_set.update({"results_count": 0})

    for c, c_d in byc["config"]["beacon_counts"].items():
        if c_d["h->o_key"] in byc["dataset_results"][ds_id]:
            r_c = byc["dataset_results"][ds_id][ c_d["h->o_key"] ]["target_count"]
            r_set["info"]["counts"].update({ c: r_c })
    if byc["empty_query_all_count"]:
        r_set.update({"results_count": byc["empty_query_all_count"] })
    elif isinstance(r_s_res, list):
        r_set.update({"results_count": len( r_s_res ) })

    return r_set

################################################################################

def check_alternative_single_set_deliveries(ds_id, r_s_res, byc):

    check_datatable_delivery(r_s_res, byc)
    check_alternative_variant_deliveries(ds_id, byc)
    check_alternative_callset_deliveries(ds_id, byc)

    return byc

################################################################################

def response_meta_add_request_summary(r, byc):

    if not "received_request_summary" in r["meta"]:
        return r

    r_rcvd_rs = r["meta"]["received_request_summary"]
    defs = byc.get("beacon_defaults", {})
    b_e_d = defs.get("entity_defaults", {})

    form = byc["form_data"]

    r_rcvd_rs.update({
        "filters": byc.get("filters", []), 
        "pagination": byc.get("pagination", {}),
        "api_version": b_e_d["info"].get("api_version", "v2")
    })

    for p in ["include_resultset_responses", "requested_granularity"]:
        if p in form:
            r_rcvd_rs.update({p:form.get(p)})
            if "requested_granularity" in p:
                r["meta"].update({"returned_granularity": form.get(p)})

    try:
        for rrs_k, rrs_v in byc["service_config"]["meta"]["received_request_summary"].items():
            r_rcvd_rs.update( {rrs_k: rrs_v })
    except:
        pass

    return r

################################################################################

def update_meta_queries(byc):

    try:
        if not "info" in byc["meta"]:
            byc["meta"].update({"info":{}})
        byc["service_response"]["meta"]["info"].update({ "processed_query": byc.get("original_queries", {}) })
    except:
        pass

    return byc

################################################################################

def create_empty_beacon_response(byc):

    r_s = byc["response_entity"].get("response_schema", None)
    if r_s is None:
        return byc

    r, e = instantiate_response_and_error(byc, r_s)
    response_update_meta(r, byc)

    try:
        r["response"].update({"result_sets":[]})
    except KeyError:
        pass

    if "beaconResultsetsResponse" in r_s:

        # TODO: stringent definition on when this is being used
        r_set = object_instance_from_schema_name(byc, "beaconResultsets", "definitions/ResultsetInstance/properties")

        if "dataset_ids" in byc:
            for ds_id in byc[ "dataset_ids" ]:
                ds_rset = r_set.copy()
                ds_rset.update({
                    "id": ds_id,
                    "set_type": "dataset",
                    "results_count": 0,
                    "exists": False,
                    "info": { "counts": { } }
                })
                r["response"]["result_sets"].append(ds_rset)

    byc.update( {"service_response": r, "error_response": e })

    # saving the parameters to the response
    for p in ["method", "dataset_ids", "filters", "variant_pars"]:
        if p in byc:
            response_add_received_request_summary_parameter(byc, p, byc[ p ])

    return byc

################################################################################

def create_empty_service_response(byc):

    r, e = instantiate_response_and_error(byc, byc["response_entity"]["response_schema"])
    response_update_meta(r, byc)

    byc.update( {"service_response": r, "error_response": e })

    # saving the parameters to the response
    for p in ["method", "dataset_ids", "filters", "variant_pars"]:
        if p in byc:
            response_add_received_request_summary_parameter(byc, p, byc[ p ])

    return byc

###############################################################################

def create_empty_non_data_response(byc):

    r, e = instantiate_response_and_error(byc, byc["response_entity"]["response_schema"])
    response_update_meta(r, byc)

    for r_k, r_v in byc["service_config"]["response"].items():
        r["response"].update({r_k: r_v})

    byc.update( {"service_response": r, "error_response": e })

    return byc

################################################################################

def check_plot_responses(ds_id, byc):

    if not "plot" in byc["output"]:
        return byc

    check_cnvhistogram_plot_response(ds_id, byc)

    return byc

################################################################################

def check_cnvhistogram_plot_response(ds_id, byc):

    ds_h_o = byc["dataset_definitions"][ ds_id ]["handoverTypes"]

    if "cnvhistogram" not in ds_h_o:
        return

    byc["include_handovers"] = True
    byc["dataset_definitions"][ ds_id ].update({"handoverTypes": ["cnvhistogram"] })
    dataset_results_save_handovers(ds_id, byc)
    r_s_ho = dataset_response_add_handovers(ds_id, byc)

    for h_o in r_s_ho:
        if "cnvhistogram" in h_o["handover_type"]["id"]:
            print_uri_rewrite_response(h_o["url"], "", "")
            exit()

    return byc

################################################################################

def check_datatable_delivery(results, byc):

    if not "table" in byc["output"]:
        return byc
    if not "datatable_mappings" in byc:
        return byc

    export_datatable_download(results, byc)

################################################################################

def instantiate_response_and_error(byc, schema):

    """The response relies on the pre-processing of input parameters (queries etc)."""
    r = object_instance_from_schema_name(byc, schema, "properties")
    m = object_instance_from_schema_name(byc, "beaconResponseMeta", "properties")
    r.update({"meta": m })
    if byc["debug_mode"] is True:
        print(byc["response_entity"]["response_schema"])
        prjsonnice(r)
    e = object_instance_from_schema_name(byc, "beaconErrorResponse", "properties")

    return r, e

################################################################################

def response_update_meta(r, byc):

    if "response_summary" in r:
        r["response_summary"].update({ "exists": False })
    response_meta_set_info_defaults(r, byc)
    response_meta_set_config_defaults(r, byc)
    response_meta_set_entity_values(r, byc)
    response_meta_add_request_summary(r, byc)
    if byc["test_mode"] is True:
        r["meta"].update({"test_mode": byc["test_mode"]})
    else:
        r["meta"].pop("test_mode", None)

################################################################################

def response_meta_set_info_defaults(r, byc):

    defs = byc.get("beacon_defaults", {})
    b_e_d = defs.get("entity_defaults", {})

    for i_k in ["api_version", "beacon_id"]:
        r["meta"].update({ i_k: b_e_d["info"].get(i_k, "") })

    return r

################################################################################

def response_meta_set_config_defaults(r, byc):

    # TODO: should be in schemas
    m = byc["service_config"].get("meta", {})
    for k, v in m.items():
        r["meta"].update( { k: v } )

    return r

################################################################################

def response_meta_set_entity_values(r, byc):
 
    try:
        r["meta"]["received_request_summary"].update({
            "requested_schemas": [ byc["response_entity"]["beacon_schema"] ]
        })
        r["meta"].update( { "returned_schemas": [ byc["response_entity"]["beacon_schema"] ] } )
    except:
        pass

    return r

################################################################################

def response_add_received_request_summary_parameter(byc, name, value):

    # TODO: proper request parameters
    if "variant_pars" in name:
        name = "request_parameters"

    if not "received_request_summary" in byc["service_response"]["meta"]:
        return byc

    if value:
        byc["service_response"]["meta"]["received_request_summary"].update( { name: value } )

    return byc

################################################################################

def response_collect_errors(byc):

    # TODO: flexible list of errors
    if not byc[ "queries" ].keys():
      response_add_error(byc, 200, "No (correct) query parameters were provided." )
    if len(byc[ "dataset_ids" ]) > 1:
      response_add_error(byc, 200, "More than 1 `datasetIds` value was provided." )
      
################################################################################

def response_add_error(byc, code=200, message=False):

    if message is False:
        return byc
    if len(str(message)) < 1:
        return byc

    e = { "error_code": code, "error_message": message }
    byc["error_response"].update({"error": e})

    return byc

################################################################################

def collations_set_delivery_keys(byc):

    # the method keys can be overriden with "deliveryKeys"

    method = byc.get("method", False)
    conf = byc["service_config"]

    d_k = form_return_listvalue( byc["form_data"], "deliveryKeys" )

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
        d_k = conf["method_keys"][ method ]

    return d_k

################################################################################

def populate_service_response( byc, results):

    populate_service_header(byc, results)
    populate_service_response_counts(byc)
    byc["service_response"]["response"].update({"results": results })

    return byc

################################################################################

def populate_service_header(byc, results):

    try:
        r_s = byc["service_response"]["response_summary"]
    except:
        return byc
    r_no = 0

    if isinstance(results, list):
        r_no = len( results )
        r_s.update({"num_total_results": r_no })
    if r_no > 0:
        r_s.update({"exists": True })

    return byc

################################################################################

def populate_service_response_counts(byc):

    if not "dataset_results" in byc:
        return byc
    if not "dataset_ids" in byc:
        return byc

    ds_id = byc["dataset_ids"][0]

    if not ds_id in byc["dataset_results"]:
        return byc

    counts = { }

    for c, c_d in byc["config"]["beacon_counts"].items():

        if c_d["h->o_key"] in byc["dataset_results"][ds_id]:
            counts[ c ] = byc["dataset_results"][ds_id][ c_d["h->o_key"] ]["target_count"]

    byc["service_response"]["info"].update({ "counts": counts })

    return byc

################################################################################

def check_alternative_variant_deliveries(ds_id, byc):

    if not "genomicVariant" in byc["response_entity_id"]:
        return byc

    if "pgxseg" in byc["output"]:
        export_pgxseg_download(ds_id, byc)

    if "variants" in byc["method"]:
        export_variants_download(ds_id, byc)

    return byc

################################################################################

def check_alternative_callset_deliveries(ds_id, byc):

    check_callsets_matrix_delivery(ds_id, byc)

    return byc

################################################################################

def return_filtering_terms_response( byc ):

    if not "filteringTerm" in byc["response_entity_id"]:
        return byc

    # TODO: correct response w/o need to fix
    byc["service_response"].update({"response": { "filteringTerms": [], "resources": []} })

    f_r_d = {}

    f_db = byc["config"]["info_db"]
    f_coll = byc["config"]["collations_coll"]

    f_t_s = [ ]
    ft_fs = [ ]

    if "filters" in byc:
        if len(byc["filters"]) > 0:
            for f in byc["filters"]:
                ft_fs.append('('+f["id"]+')')
    f_s = '|'.join(ft_fs)
    f_re = re.compile(r'^'+f_s)

    collation_types = set()

    for ds_id in byc[ "dataset_ids" ]:

        query = { "dataset_id": ds_id }

        try:
            if len(byc["form_data"]["scope"]) > 4:
                query.update({"scope": byc["form_data"]["scope"]})
        except:
            pass

        fields = { "_id": 0 }

        f_s, e = mongo_result_list(f_db, f_coll, query, fields)

        t_f_t_s = [ ]

        for f in f_s:
            collation_types.add(f.get("collation_type", None))
            f_t = { "count": f.get("count", 0)}
            for k in ["id", "type", "label"]:
                if k in f:
                    f_t.update({k:f[k]})
            t_f_t_s.append(f_t)

        f_t_s.extend(t_f_t_s)

    byc["service_response"]["response"].update({ "filteringTerms": f_t_s })
    byc["service_response"]["response"].update({ "resources": create_filters_resource_response(collation_types, byc) })

    cgi_print_response( byc, 200 )

################################################################################

def create_filters_resource_response(collation_types, byc):

    r_o = {}
    resources = []

    f_d_s = byc["filter_definitions"]
    collation_types = list(collation_types)
    res_schema = object_instance_from_schema_name(byc, "beaconFilteringTermsResults", "definitions/Resource/properties", "json")    
    for c_t in collation_types:
        f_d = f_d_s[c_t]
        r = {}
        for k in res_schema.keys():
            if k in f_d:
                r.update({k:f_d[k]})

        r_o.update( {f_d["namespace_prefix"]: r })

    for k, v in r_o.items():
        resources.append(v)
    return resources

################################################################################

def check_computed_interval_frequency_delivery(byc):

    if not "frequencies" in byc["output"]:
        return byc

    ds_id = byc[ "dataset_ids" ][ 0 ]
    ds_results = byc["dataset_results"][ds_id]
    p_r = byc["pagination"]

    if not "callsets._id" in ds_results:
        return byc

    cs_r = ds_results["callsets._id"]

    mongo_client = MongoClient()
    cs_coll = mongo_client[ ds_id ][ "callsets" ]

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
        print('#meta=>"WARNING: Only analyses {} - {} (out of {}) used for calculations due to pagination skip and limit"'.format((p_r["range"][0] + 1), p_r["range"][-1], cs_r["target_count"]))

    h_ks = ["reference_name", "start", "end", "gain_frequency", "loss_frequency", "no"]
    print("group_id\t"+"\t".join(h_ks))

    cs_cursor = cs_coll.find({"_id": {"$in": q_vals }, "variant_class": { "$ne": "SNV" } } )

    intervals, cnv_cs_count = interval_counts_from_callsets(cs_cursor, byc)
    for intv in intervals:
        v_line = [ ]
        v_line.append("query_result")
        for k in h_ks:
            v_line.append(str(intv[k]))
        print("\t".join(v_line))

    close_text_streaming()

################################################################################

def check_callsets_matrix_delivery(ds_id, byc):

    if not "pgxmatrix" in byc["output"]:
        return byc

    export_callsets_matrix(ds_id, byc)
        