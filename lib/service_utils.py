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
from handover_execution import handover_return_data
from handover_generation import dataset_response_add_handovers, query_results_save_handovers
from interval_utils import generate_genomic_intervals, interval_counts_from_callsets
from query_execution import execute_bycon_queries, process_empty_request, mongo_result_list
from query_generation import  initialize_beacon_queries, replace_queries_in_test_mode
from read_specs import read_bycon_configs_by_name,read_local_prefs
from schemas_parser import *
from variant_responses import normalize_variant_values_for_export

################################################################################

def initialize_bycon():

    byc =  {
        "service_name": "beacon",
        "service_id": "beacon",
        "response_entity": {
            "entity_type": "dataset",
            "collection": "dbstats",
            "response_schema": "progenetixServiceResponse",
            "beacon_schema": {
                "entity_type": "dataset",
                "schema": "https://progenetix.org/services/schemas/dataset/"
            },
            "h->o_access_key": False
        },
        "beacon_info": {},
        "pkg_path": pkg_path,
        "method": "",
        "output": "",
        "form_data": {},
        "query_meta": {},
        "debug_state": False,
        "empty_query_all_response": False,
        "empty_query_all_count": False,
        "test_mode": False,    
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
    form = byc["form_data"]

    if "bycon_definition_files" in conf:
        for d in conf["bycon_definition_files"]:
            read_bycon_configs_by_name( d, byc )

    if "defaults" in conf:
        for d_k, d_v in conf["defaults"].items():
            byc.update( { d_k: d_v } )

    if not "pagination" in byc:
        byc.update( { "pagination": {"skip": 0, "limit": 0 } } )

    for sp in ["skip", "limit"]:
        if sp in form["pagination"]:
            if form["pagination"][sp] > 0:
                byc["pagination"].update({sp: form["pagination"][sp]})

    if "output" in form:
        byc["output"] = form["output"]

    if "method" in form:
        if "method_keys" in conf:
            m = form.get("method", "___none___")
            if m in conf["method_keys"].keys():
                byc["method"] = m

    test_mode = form.get("testMode", None)
    if test_mode:
        byc.update({"test_mode": True })

    # TODO: standardize the general defaults / entity defaults / form values merging
    #       through pre-parsing into identical structures and then use deepmerge etc.

    return byc

################################################################################

def run_result_sets_beacon(byc):

    sr_r = byc["service_response"]["response"]

    ######## result sets loop ##################################################

    for i, r_set in enumerate(sr_r["result_sets"]):

        # TODO: put this into function
        r_set.update({"results_count": 0})
        ds_id = r_set["id"]

        # TODO: beter definition of when to query
        check_empty_query_all_response(byc)
        execute_bycon_queries( ds_id, byc )
        r_s_res = retrieve_data(ds_id, byc)
        r_set.update({ "results_handovers": dataset_response_add_handovers(ds_id, byc) })

        for c, c_d in byc["config"]["beacon_counts"].items():
            if c_d["h->o_key"] in byc["dataset_results"][ds_id]:
                r_c = byc["dataset_results"][ds_id][ c_d["h->o_key"] ]["target_count"]
                r_set["info"]["counts"].update({ c: r_c })
        if byc["empty_query_all_count"]:
            r_set.update({"results_count": byc["empty_query_all_count"] })
        elif isinstance(r_s_res, list):
            r_set.update({"results_count": len( r_s_res ) })

        if r_set["results_count"] < 1:
            continue

        r_s_res = remap_variants(r_s_res, byc)
        r_s_res = remap_analyses(r_s_res, byc)
        r_s_res = remap_biosamples(r_s_res, byc)
        r_s_res = remap_runs(r_s_res, byc)
        r_s_res = remap_all(r_s_res)
        results_pagination_range(len(r_s_res), byc)
        r_s_res = paginate_results(r_s_res, byc)

        r_set.update({"paginated_results_count": len( r_s_res ) })

        r_set.update({ "exists": True, "results": r_s_res })

    ######## end of result sets loop ###########################################

    sr_rs = byc["service_response"]["response_summary"]
    for r_set in sr_r["result_sets"]:
        sr_rs["num_total_results"] += r_set["results_count"]

    if sr_rs["num_total_results"] > 0:
        sr_rs.update({"exists": True })

    return byc

################################################################################

def check_empty_query_all_response(byc):

    if len(byc["queries"].keys()) > 0:
        return byc

    byc.update({ "empty_query_all_response": True })
    byc["service_response"]["meta"]["received_request_summary"].update({"include_resultset_responses":"ALL"})
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

def results_pagination_range(count, byc):

    r_range = [
        byc["pagination"]["skip"] * byc["pagination"]["limit"],
        byc["pagination"]["skip"] * byc["pagination"]["limit"] + byc["pagination"]["limit"],
    ]

    r_l_i = count - 1

    if r_range[0] > r_l_i:
        r_range[0] = r_l_i
    if r_range[-1] > count:
        r_range[-1] = count

    byc["pagination"].update({"range":r_range})

    return byc

################################################################################

def paginate_results(results, byc):

    if byc["pagination"]["limit"] < 1:
        return results

    r = byc["pagination"]["range"]

    results = results[r[0]:r[-1]]

    return results

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

    r, e = instantiate_response_and_error(byc)

    response_update_meta(r, byc)

    try:
        if len(byc["this_config"]["defaults"]["include_resultset_responses"]) > 2:
            r.update({"result_sets":[]})
    except KeyError:
        pass

    if "beaconResultsetsResponse" in byc["response_entity"]["response_schema"]:

        # TODO: stringent definition on when this is being used

        r_set_s = read_schema_files("beaconResultSets", "definitions/resultSetInstance/properties", byc)
        r_set = create_empty_instance(r_set_s)
   
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

    r, e = instantiate_response_and_error(byc)

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

    r, e = instantiate_response_and_error(byc)

    response_update_meta(r, byc)

    for r_k, r_v in byc["this_config"]["response"].items():
        r["response"].update({r_k: r_v})

    byc.update( {"service_response": r, "error_response": e })

    return byc

################################################################################

def check_switch_to_plot_response(byc):

    if not "plot" in byc["output"]:
        return
    if not "result_sets" in byc["service_response"]["response"]:
        return

    h_o_s = byc["service_response"]["response"]["result_sets"][0]["results_handovers"]

    for h_o in h_o_s:
        if "cnvhistogram" in h_o["handoverType"]["id"]:
            cgi_print_rewrite_response(h_o["url"], "", "")
            exit()

    return

################################################################################

def instantiate_response_and_error(byc):

    """The response relies on the pre-processing of input parameters (queries etc)."""
    r_s = read_schema_files(byc["response_entity"]["response_schema"], "properties", byc)
    r = create_empty_instance(r_s)

    e_s = read_schema_files("beaconErrorResponse", "properties", byc)
    e = create_empty_instance(e_s)

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
        r["meta"].update({ i_k: byc["beacon_info"].get(i_k, "") })

    return r

################################################################################

def response_meta_set_config_defaults(r, byc):
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
        b_mps = byc["m_k"]
        if byc["query_meta"]["requested_schemas"][0]:
            if "entityType" in byc["query_meta"]["requested_schemas"][0]:
                e_t = byc["query_meta"]["requestedSchemas"][0]["entityType"]
                for rd in b_mps["response_types"]:
                    if r_d["entity_type"] == e_t:
                        byc.update({"response_type":e_t})
    except:
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

def check_alternative_variant_deliveries(byc):

    if not "variant" in byc["response_type"]:
        return byc

    try:
        first_ds_id = byc["service_response"]["response"]["result_sets"][0].get("id", "progenetix")
    except:
        first_ds_id = "progentix"
        
    if "pgxseg" in byc["output"]:
        export_pgxseg_download(first_ds_id, byc)

    if "variants" in byc["method"]:
        export_variants_download(first_ds_id, byc)

    return byc

################################################################################

def return_filtering_terms_response( byc ):

    if not "filteringTerm" in byc["response_type"]:
        return byc

    # TODO: correct response w/o need to fix
    byc["service_response"].update({"response": { "filteringTerms": [], "resources": []} })

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

    # r_s_l = {}

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
            f_t = { "count": f.get("count", 0)}
            for k in ["id", "type", "label"]:
                f_t.update({k:f.get(k, 0)})
            t_f_t_s.append(f_t)

            # r_id = {


            # }

            # r_s_l.update({})

        f_t_s.extend(t_f_t_s)

    byc["service_response"]["response"].update({ "filteringTerms": f_t_s })
    byc["service_response"]["response"].update({ "resources": _create_resource_response(byc) })

    cgi_print_response( byc, 200 )

################################################################################

def _create_resource_response(byc):

    r_o = {}
    resources = []

    for res in byc["filter_definitions"].values():

        r_o.update(
            {res["name_space_prefix"]: {
                "id": res.get("name_space_prefix", "").lower(),
                "name": res.get("name", ""),
                "name_space_prefix": res.get("name_space_prefix", ""),
                "url": res.get("url", "")
            }
        })

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
        q_vals = paginate_results(q_vals, byc)
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

def check_callsets_matrix_delivery(byc):

    if not "pgxmatrix" in byc["output"]:
        return byc

    m_format = "coverage"
    if "val" in byc["output"]:
        m_format = "values"

    ds_id = byc[ "dataset_ids" ][ 0 ]
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
        q_vals = paginate_results(q_vals, byc)
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

def print_pgx_column_header(ds_id, byc):

    if not "pgxseg" in byc["output"] and not "pgxmatrix" in byc["output"]:
        return

    mongo_client = MongoClient()
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]
    cs_coll = mongo_client[ ds_id ][ "callsets" ]

    ds_results = byc["dataset_results"][ds_id]

    open_text_streaming()

    for d in ["id", "assemblyId"]:
        print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    for m in ["variantCount", "biosampleCount"]:
        if m in byc["service_response"]["response"]["result_sets"][0]["info"]["counts"]:
            print("#meta=>{}={}".format(m, byc["service_response"]["response"]["result_sets"][0]["info"]["counts"][m]))
            
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

    open_json_streaming(byc, "variants.json")

    for v_id in ds_results["variants._id"]["target_values"][:-1]:
        v = v_coll.find_one( { "_id": v_id }, { "_id": 0 } )
        print(json.dumps(camelize(v), indent=None, sort_keys=False, default=str, separators=(',', ':')), end = ',')
    v = v_coll.find_one( { "_id": ds_results["variants._id"]["target_values"][-1]}, { "_id": -1 }  )
    print(json.dumps(camelize(v), indent=None, sort_keys=False, default=str, separators=(',', ':')), end = '')

    close_json_streaming()


################################################################################

def export_pgxseg_download(ds_id, byc):

    data_client = MongoClient( )
    v_coll = data_client[ ds_id ][ "variants" ]
    ds_results = byc["dataset_results"][ds_id]

    print_pgx_column_header(ds_id, byc)

    for v_id in ds_results["variants._id"]["target_values"]:
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
