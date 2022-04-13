from os import path, pardir
import inspect, json
import random
from pymongo import MongoClient
from bson import json_util
from humps import camelize, decamelize

# local
bycon_lib_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( bycon_lib_path, pardir )

from beacon_response_remaps import *
from cgi_parse import *
from datatable_utils import check_datatable_delivery
from handover_execution import handover_return_data
from handover_generation import dataset_response_add_handovers, query_results_save_handovers, dataset_results_save_handovers
from interval_utils import generate_genomic_intervals, interval_counts_from_callsets
from parse_variants import translate_reference_ids
from query_execution import execute_bycon_queries, process_empty_request, mongo_result_list
from query_generation import  initialize_beacon_queries, paginate_list, replace_queries_in_test_mode, set_pagination_range
from read_specs import read_bycon_configs_by_name,read_local_prefs
from schemas_parser import *
from variant_responses import normalize_variant_values_for_export

################################################################################

def initialize_bycon():

    byc =  {
        "service_name": "beacon",
        "service_id": "beacon",
        "response_entity": {},
        "beacon_info": {},
        "beacon_base_paths": [],
        "pkg_path": pkg_path,
        "method": "",
        "output": "",
        "form_data": {},
        "query_meta": {},
        "include_handovers": False,
        "debug_mode": False,
        "empty_query_all_response": False,
        "empty_query_all_count": False,
        "test_mode": False,  
        "debug_mode": False,  
        "errors": [],
        "warnings": []
    }

    return byc

################################################################################

def run_beacon_init_stack(byc):

    beacon_get_endpoint_base_paths(byc)
    initialize_beacon_queries(byc)
    print_parameters_response(byc)
    generate_genomic_intervals(byc)
    create_empty_beacon_response(byc)
    replace_queries_in_test_mode(byc, 5)
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    return byc

################################################################################

def initialize_service(byc, service=False):

    """For consistency, the name of the local configuration file should usually
    correspond to the calling main function. However, an overwrite can be
    provided."""

    # print(config)

    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    sub_path = path.dirname( path.abspath(mod.__file__) )

    if service is False:
        service = frm.function

    service = decamelize(service)

    byc.update({
        "service_name": path.splitext(path.basename(mod.__file__))[0],
        "service": service
    })

    read_local_prefs( service, sub_path, byc )

    conf = byc["this_config"]
    defs = byc["beacon_defaults"]
    form = byc["form_data"]

    if "bycon_definition_files" in defs:
        for d in defs["bycon_definition_files"]:
            read_bycon_configs_by_name( d, byc )

    if "defaults" in conf:
        for d_k, d_v in conf["defaults"].items():
            byc.update( { d_k: d_v } )
    if "defaults" in defs:
        for d_k, d_v in defs["defaults"].items():
            byc.update( { d_k: d_v } )

    if service in defs:
        for d_k, d_v in defs[ service ].items():
            byc.update( { d_k: d_v } )

    if not "pagination" in byc:
        byc.update( { "pagination": {"skip": 0, "limit": 0 } } )

    for sp in ["skip", "limit"]:
        if sp in form["pagination"]:
            if form["pagination"][sp] > -1:
                byc["pagination"].update({sp: form["pagination"][sp]})

    byc["output"] = form.get("output", "")

    # TODO: this is only used in some services ...
    if "method_keys" in conf:
        m = form.get("method", "___none___")
        if m in conf["method_keys"].keys():
            byc["method"] = m

    translate_reference_ids(byc)
    
    byc.update({"test_mode": test_truthy( form.get("testMode", "false") ) })
    byc.update({"include_handovers": test_truthy( form.get("include_handovers", "false") ) })

    # TODO: standardize the general defaults / entity defaults / form values merging
    #       through pre-parsing into identical structures and then use deepmerge etc.

    return byc

################################################################################

def run_result_sets_beacon(byc):
    
    sr_r = byc["service_response"]["response"]

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
        
        if test_truthy( byc["form_data"].get("paginateResults", True) ):
            r_s_res = paginate_list(r_s_res, byc)

        check_alternative_single_set_deliveries(ds_id, r_s_res, byc)
        r_s_res = reshape_resultset_results(ds_id, r_s_res, byc)

        r_set.update({
            "paginated_results_count": len( r_s_res ),
            "exists": True,
            "results": r_s_res
        })

    ######## end of result sets loop ###########################################

    sr_rs = byc["service_response"]["response_summary"]
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

def retrieve_data(ds_id, byc):

    r_c = byc["response_entity"]["collection"]
    r_k = r_c+"_id"

    for r_d in byc["beacon_mappings"]["response_types"]:
        if r_d["entity_type"] == byc["response_type"]:
            r_k = r_d["h->o_access_key"]

    if "variants" in r_c:
        r_s_res = retrieve_variants(ds_id, byc)
        return r_s_res

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    data_coll = mongo_client[ ds_id ][ r_c ]

    ds_results = byc["dataset_results"][ds_id]

    if r_k in ds_results:
        r_s_res = []
        for d in data_coll.find({"_id":{"$in": ds_results[ r_k ]["target_values"] }}):
            r_s_res.append(d)

        return r_s_res

    return []

################################################################################

def retrieve_variants(ds_id, byc):

    ds_results = byc["dataset_results"][ds_id]

    if "all_variants_methods" in byc["this_config"]:
        if byc["method"] in byc["this_config"]["all_variants_methods"]:
            return False

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    v_coll = mongo_client[ ds_id ][ "variants" ]

    r_s_res = []

    if "variants._id" in ds_results:
        for v_id in ds_results["variants._id"]["target_values"]:
            v = v_coll.find_one({"_id":v_id})
            r_s_res.append(v)
        return r_s_res
    elif "variants.variant_internal_id" in ds_results:
        for v_id in ds_results["variants.variant_internal_id"]["target_values"]:
            vs = v_coll.find({"variant_internal_id":v_id})
            for v in vs:
                r_s_res.append(v)
        return r_s_res

    return False

################################################################################

def response_meta_add_request_summary(r, byc):

    if not "received_request_summary" in r["meta"]:
        return r

    form = byc["form_data"]

    r["meta"]["received_request_summary"].update({
        "filters": byc.get("filters", []), 
        "pagination": byc.get("pagination", {}),
        "api_version": byc["beacon_info"].get("api_version", "v2")
    })

    for p in ["include_resultset_responses", "requested_granularity"]:
        if p in form:
            r["meta"]["received_request_summary"].update({p:form.get(p)})
            if "requested_granularity" in p:
                r["meta"].update({"returned_granularity": form.get(p)})

    try:
        for rrs_k, rrs_v in byc["this_config"]["meta"]["received_request_summary"].items():
            r["meta"]["received_request_summary"].update( {rrs_k: rrs_v })
    except:
        pass

    # TODO: This is a private extension so far.
    r["meta"]["received_request_summary"].update({ "processed_query": byc.get("queries", {}) })

    return r

################################################################################

def create_empty_beacon_response(byc):

    response_update_type_from_request(byc, "beacon")
    response_set_entity(byc, "beacon")

    r, e = instantiate_response_and_error(byc, byc["response_entity"]["response_schema"])

    response_update_meta(r, byc)

    try:
        r["response"].update({"result_sets":[]})
    except KeyError:
        pass

    if "beaconResultsetsResponse" in byc["response_entity"]["response_schema"]:

        # TODO: stringent definition on when this is being used
        r_set = object_instance_from_schema_name(byc, "resultsetInstance", "properties")

        # print(r_set)
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

    response_update_type_from_request(byc, "service")
    response_set_entity(byc, "service")

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

    response_update_type_from_request(byc, "beacon")
    response_set_entity(byc)

    r, e = instantiate_response_and_error(byc, byc["response_entity"]["response_schema"])

    response_update_meta(r, byc)

    for r_k, r_v in byc["this_config"]["response"].items():
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
            cgi_print_rewrite_response(h_o["url"], "", "")
            exit()

    return byc

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
    r["meta"].update({"test_mode": byc["test_mode"]})

################################################################################

def print_parameters_response(byc):

    if not "queries" in byc:
        return byc

    if not byc["service_id"] in byc["queries"].keys():
        return byc

    s_i_d = byc["service_id"]

    try:
        if "requestParameters" in byc["queries"][ s_i_d ]["id"]:
            cgi_print_json_response(byc["this_request_parameters"])
        elif "endpoints" in byc["queries"][ s_i_d ]["id"]:
            cgi_print_json_response(byc["this_endpoints"])
    except:
        pass

    return byc

################################################################################

def response_meta_set_info_defaults(r, byc):

    for i_k in ["api_version", "beacon_id", "create_date_time", "update_date_time"]:
#DEBUG        print(byc["beacon_info"].get(i_k, ""))
        r["meta"].update({ i_k: byc["beacon_defaults"]["info"].get(i_k, "") })

    return r

################################################################################

def response_meta_set_config_defaults(r, byc):

    # TODO: should be in schemas

    if "meta" in byc["this_config"]:
        for k, v in byc["this_config"]["meta"].items():
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

def response_update_type_from_request(byc, scope="beacon"):

    m_k = str(scope) + "_mappings"

    try:
        b_mps = byc[m_k]["response_types"]
        if byc["query_meta"]["requested_schemas"][0]:
            r_s = byc["query_meta"]["requested_schemas"][0]
            if "entityType" in r_s:
                e_t = r_s["entityType"]
                for r_d in b_mps:
                    if r_d["entity_type"] == e_t:
                        byc.update({"response_type":e_t})
                        byc["query_meta"].update({"requested_schemas": r_d["beacon_schema"]})
    except Exception as e:
        pass

    return byc

################################################################################

def response_add_received_request_summary_parameter(byc, name, value):

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

def response_add_error(byc, code=200, message=""):

    e = { "error_code": code, "error_message": message }

    byc["error_response"]["error"].update(e)

    return byc

################################################################################

def response_set_entity(byc, scope="beacon"):

    m_k = str(scope) + "_mappings"

    try:
        for r_d in byc[m_k]["response_types"]:
            # print(r_d["entity_type"], byc["response_type"])
            
            if r_d["entity_type"] == byc["response_type"]:
                byc.update({"response_entity": r_d })
                return byc
    except:
        pass

    return byc

################################################################################

def collations_set_delivery_keys(byc):

    # the method keys can be overriden with "deliveryKeys"

    method = byc.get("method", False)
    conf = byc["this_config"]

    d_k = form_return_listvalue( byc["form_data"], "deliveryKeys" )

    if len(d_k) > 0:
        return d_k

    if method is False:
        return d_k

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
        response_add_error(byc, 200)

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

    if not "variant" in byc["response_type"]:
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

    if not "filteringTerm" in byc["response_type"]:
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

    open_text_streaming("interval_cnv_frequencies.pgxseg")

    for d in ["id", "assemblyId"]:
        print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    _print_filters_meta_line(byc)
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

    cs_cursor = cs_coll.find({"_id": {"$in": q_vals } } )

    intervals = interval_counts_from_callsets(cs_cursor, byc)
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

    m_format = "coverage"
    if "val" in byc["output"]:
        m_format = "values"

    ds_results = byc["dataset_results"][ds_id]
    p_r = byc["pagination"]

    if not "callsets._id" in ds_results:
        return byc

    cs_r = ds_results["callsets._id"]

    mongo_client = MongoClient()
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]
    cs_coll = mongo_client[ ds_id ][ "callsets" ]

    open_text_streaming("interval_callset_matrix.pgxmatrix")

    for d in ["id", "assemblyId"]:
        print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    _print_filters_meta_line(byc)
    print("#meta=>data_format=interval_"+m_format)

    info_columns = [ "analysis_id", "biosample_id", "group_id" ]
    h_line = interval_header(info_columns, byc)
    print("#meta=>genome_binning={};interval_number={}".format(byc["genome_binning"], len(byc["genomic_intervals"])) )
    print("#meta=>no_info_columns={};no_interval_columns={}".format(len(info_columns), len(h_line) - len(info_columns)))

    q_vals = cs_r["target_values"]
    r_no = len(q_vals)
    if r_no > p_r["limit"]:
        if test_truthy( byc["form_data"].get("paginateResults", True) ):
            q_vals = paginate_list(q_vals, byc)
        print('#meta=>"WARNING: Only analyses {} - {} (from {}) will be included pagination skip and limit"'.format((p_r["range"][0] + 1), p_r["range"][-1], cs_r["target_count"]))

    bios_ids = set()
    cs_ids = {}
    cs_cursor = cs_coll.find({"_id": {"$in": q_vals } } )
    for cs in cs_cursor:
        bios = bs_coll.find_one( { "id": cs["biosample_id"] } )
        bios_ids.add(bios["id"])
        s_line = "#sample=>biosample_id={};analysis_id={}".format(bios["id"], cs["id"])
        h_d = bios["histological_diagnosis"]
        cs_ids.update({cs["id"]: h_d.get("id", "NA")})
        s_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(s_line, h_d.get("id", "NA"), h_d.get("label", "NA"), h_d.get("id", "NA"), h_d.get("label", "NA"))
        print(s_line)

    print("#meta=>biosampleCount={};analysisCount={}".format(len(bios_ids), cs_r["target_count"]))
    print("\t".join(h_line))

    for cs_id, group_id in cs_ids.items():
        cs = cs_coll.find_one({"id":cs_id})
        if "values" in m_format:
            print("\t".join(
                [
                    cs_id,
                    cs.get("biosample_id", "NA"),
                    group_id,
                    *map(str, cs["cnv_statusmaps"]["max"]),
                    *map(str, cs["cnv_statusmaps"]["min"])
                ]
            ))
        else:
            print("\t".join(
                [
                    cs_id,
                    cs.get("biosample_id", "NA"),
                    group_id,
                    *map(str, cs["cnv_statusmaps"]["dup"]),
                    *map(str, cs["cnv_statusmaps"]["del"])
                ]
            ))

    close_text_streaming()
        
################################################################################

def print_pgx_column_header(ds_id, ds_results, byc):

    if not "pgxseg" in byc["output"] and not "pgxmatrix" in byc["output"]:
        return

    s_r_rs = byc["service_response"]["response"]["result_sets"][0]
    b_p = byc["pagination"]

    mongo_client = MongoClient()
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]
    cs_coll = mongo_client[ ds_id ][ "callsets" ]

    open_text_streaming()

    for d in ["id", "assemblyId"]:
        print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    for k, n in s_r_rs["info"]["counts"].items():
        print("#meta=>{}={}".format(k, n))
    print("#meta=>pagination.skip={};pagination.limit={};pagination.range={},{}".format(b_p["skip"], b_p["skip"], b_p["range"][0] + 1, b_p["range"][1]))
            
    _print_filters_meta_line(byc)

    for bs_id in ds_results["biosamples.id"][ "target_values" ]:
        bs = bs_coll.find_one( { "id": bs_id } )
        h_line = "#sample=>biosample_id={}".format(bs_id)
        h_d = bs["histological_diagnosis"]
        h_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(h_line, h_d.get("id", "NA"), h_d.get("label", "NA"), h_d.get("id", "NA"), h_d.get("label", "NA"))
        print(h_line)

    print("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format("biosample_id", "reference_name", "start", "end", "log2", "variant_type", "reference_bases", "alternate_bases" ) )

    return

################################################################################

def _print_filters_meta_line(byc):

    if "filters" in byc["service_response"]["meta"]["received_request_summary"]:
        f_vs = []
        for f in byc["service_response"]["meta"]["received_request_summary"]["filters"]:
            f_vs.append(f["id"])
        print("#meta=>filters="+','.join(f_vs))

    return

################################################################################

def export_variants_download(ds_id, byc):

    data_client = MongoClient( )
    v_coll = data_client[ ds_id ][ "variants" ]
    ds_results = byc["dataset_results"][ds_id]
 
    v__ids = byc["dataset_results"][ds_id]["variants._id"].get("target_values", [])
    if test_truthy( byc["form_data"].get("paginateResults", True) ):
        v__ids = paginate_list(v__ids, byc)

    open_json_streaming(byc, "variants.json")

    for v_id in v__ids[:-1]:
        v = v_coll.find_one( { "_id": v_id }, { "_id": 0 } )
        print(decamelize_words(json.dumps(camelize(v), indent=None, sort_keys=False, default=str, separators=(',', ':')), end = ','))
    v = v_coll.find_one( { "_id": v__ids[-1]}, { "_id": 0 }  )
    print(decamelize_words(json.dumps(camelize(v), indent=None, sort_keys=False, default=str, separators=(',', ':')), end = ''))

    close_json_streaming()

################################################################################

def export_pgxseg_download(ds_id, byc):

    data_client = MongoClient( )
    v_coll = data_client[ ds_id ][ "variants" ]
    ds_results = byc["dataset_results"][ds_id]
    v__ids = byc["dataset_results"][ds_id]["variants._id"].get("target_values", [])
    if test_truthy( byc["form_data"].get("paginateResults", True) ):
        v__ids = paginate_list(v__ids, byc)

    print_pgx_column_header(ds_id, ds_results, byc)

    for v_id in v__ids:
        v = v_coll.find_one( { "_id": v_id} )
        print_variant_pgxseg(v, byc)

    close_text_streaming()

################################################################################

def interval_header(info_columns, byc):

    int_line = info_columns.copy()

    for iv in byc["genomic_intervals"]:
        int_line.append("{}:{}-{}:DUP".format(iv["reference_name"], iv["start"], iv["end"]))
    for iv in byc["genomic_intervals"]:
        int_line.append("{}:{}-{}:DEL".format(iv["reference_name"], iv["start"], iv["end"]))

    return int_line

################################################################################

def print_variant_pgxseg(v, byc):

    drop_fields = ["_id", "info"]

    v = de_vrsify_variant(v, byc)

    if not "variant_type" in v:
        return

    v = normalize_variant_values_for_export(v, byc, drop_fields)

    if not "log2" in v:
        v["log2"] = "."
    try:
        v["start"] = int(v["start"])
    except:
        v["start"] = "."
    try:
        v["end"] = int(v["end"])
    except:
        v["end"] = "."
    if not "reference_bases" in v:
        v["reference_bases"] = "."
    if not "alternate_bases" in v:
        v["alternate_bases"] = "."
    print("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(v["biosample_id"], v["reference_name"], v["start"], v["end"], v["log2"], v["variant_type"], v["reference_bases"], v["alternate_bases"]) )
