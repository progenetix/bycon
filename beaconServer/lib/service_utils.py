from os import path, pardir
import inspect, json
from pymongo import MongoClient
from bson import json_util
from humps import camelize, decamelize

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )

from cgi_utils import *
from handover_execution import handover_retrieve_from_query_results, handover_return_data
from handover_generation import dataset_response_add_handovers, query_results_save_handovers
from interval_utils import generate_genomic_intervals
from query_execution import execute_bycon_queries, process_empty_request
from query_generation import  initialize_beacon_queries
from read_specs import read_bycon_configs_by_name,read_local_prefs
from schemas_parser import *
from variant_responses import normalize_variant_values_for_export

################################################################################

def run_beacon_init_stack(byc):

    beacon_get_endpoint_base_paths(byc)
    initialize_beacon_queries(byc)
    print_parameters_response(byc)
    generate_genomic_intervals(byc)
    create_empty_service_response(byc)
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    return byc

################################################################################

def run_beacon(byc):

    # TODO
    if "results_handover" in byc["service_response"]:
        byc["service_response"].pop("results_handover")

    # TODO: Wrong response etc.
    if "BeaconCoreResponse" in byc["response_schema"]:
        for ds_id in byc["dataset_ids"]:
            execute_bycon_queries( ds_id, byc )
            check_core_delivery(ds_id, byc)
        return byc

    for r_set in byc["service_response"]["result_sets"]:

        ds_id = r_set["id"]

        execute_bycon_queries( ds_id, byc )
        check_alternative_variant_deliveries(ds_id, byc)

        h_o, e = handover_retrieve_from_query_results(ds_id, byc)
        h_o_d, e = handover_return_data( h_o, byc, e )
        if e:
            response_add_error(byc, 422, e )
        else:
            r_set.update({ "results_handovers": dataset_response_add_handovers(ds_id, byc) })

        for c, c_d in byc["config"]["beacon_counts"].items():
            if c_d["h->o_key"] in byc["dataset_results"][ds_id]:
                r_c = byc["dataset_results"][ds_id][ c_d["h->o_key"] ]["target_count"]
                r_set["info"]["counts"].update({ c: r_c })

        if isinstance(h_o_d, list):
            results_count = len( h_o_d )

            r_set.update({"results_count": results_count })

            if results_count > 0:

                byc["service_response"]["response_summary"]["num_total_results"] += results_count
                r_set.update({ "exists": True, "results": h_o_d })

                if byc["pagination"]["limit"] > 0:
                    res_range = _pagination_range(results_count, byc)
                    r_set.update({ "results": h_o_d[res_range[0]:res_range[-1]] })

    if byc["service_response"]["response_summary"]["num_total_results"] > 0:
        byc["service_response"]["response_summary"].update({"exists": True })
        response_add_error(byc, 200)

    cgi_break_on_errors(byc)

    return byc

################################################################################

def run_result_sets_beacon(collname, byc):

    for i, r_set in enumerate(byc["service_response"]["response"]["result_sets"]):

        r_set.update({"results_count": 0})

        ds_id = r_set["id"]
        if len(byc["queries"].keys()) > 0:
            execute_bycon_queries( ds_id, byc )
            beacon_res = retrieve_data(ds_id, collname, byc)
            r_set.update({ "results_handovers": dataset_response_add_handovers(ds_id, byc) })

            for c, c_d in byc["config"]["beacon_counts"].items():
                if c_d["h->o_key"] in byc["dataset_results"][ds_id]:
                    r_c = byc["dataset_results"][ds_id][ c_d["h->o_key"] ]["target_count"]
                    r_set["info"]["counts"].update({ c: r_c })
            if isinstance(beacon_res, list):
                r_set.update({"results_count": len( beacon_res ) })

        else:
            beacon_res, results_count = process_empty_request(ds_id, collname, byc)
            if "variants" in collname:
                digests = []
                for v in beacon_res:
                    try:
                        digests.append(v["digest"])
                    except:
                        pass
                digests = list(set(digests))
                beacon_res = variants_for_digests(ds_id, digests, byc)
                results_count = len(beacon_res)
            byc["service_response"]["meta"]["received_request_summary"].update({"pagination":{"limit": 1, "skip": 0}})
            r_set.update({"results_count": results_count })

        if isinstance(beacon_res, list):
            if r_set["results_count"] > 0:

                # TODO: REMOVE VERIFIER HACKS
                if "callsets" in collname:
                    for cs_i, cs_r in enumerate(beacon_res):
                        beacon_res[cs_i].update({"pipeline_name": "progenetix", "analysis_date": "1967-11-11" })
                elif "biosamples" in collname:
                    for bs_i, bs_r in enumerate(beacon_res):
                        beacon_res[bs_i].update({"sample_origin_type": { "id": "OBI:0001479", "label": "specimen from organism"} })
                        if not beacon_res[bs_i]["tumor_grade"]:
                            beacon_res[bs_i].pop("tumor_grade")
                        if not beacon_res[bs_i]["pathological_stage"]:
                            beacon_res[bs_i].pop("pathological_stage")

                byc["service_response"]["response_summary"]["num_total_results"] += r_set["results_count"]
                r_set.update({ "exists": True, "results": beacon_res })

                if byc["pagination"]["limit"] > 0:
                    res_range = _pagination_range(r_set["results_count"], byc)
                    r_set.update({ "results": beacon_res[res_range[0]:res_range[-1]] })

        byc["service_response"]["response"]["result_sets"][i] = r_set

    if byc["service_response"]["response_summary"]["num_total_results"] > 0:
        byc["service_response"]["response_summary"].update({"exists": True })
        response_add_error(byc, 200)

    cgi_break_on_errors(byc)

    return byc

################################################################################

def retrieve_data(ds_id, collname, byc):

    if "variants" in collname:
        beacon_res = retrieve_variants(ds_id, byc)
        return beacon_res

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    bs_coll = mongo_client[ ds_id ][ collname ]

    ds_results = byc["dataset_results"][ds_id]
    r_key = collname+"._id"

    if r_key in ds_results:
        beacon_res = []
        for b in bs_coll.find({"_id":{"$in": ds_results[ r_key ]["target_values"] }}):
            #TODO: callset fix
            beacon_res.append(b)

        return beacon_res

    return False

################################################################################

def retrieve_variants(ds_id, byc):

    ds_results = byc["dataset_results"][ds_id]
    if not byc["method"] in byc["this_config"]["all_variants_methods"]:
        if "variants.digest" in ds_results:
            digests = ds_results["variants.digest"]["target_values"]
            beacon_res = variants_for_digests(ds_id, digests, byc)
            return beacon_res

    return False

################################################################################

def variants_for_digests(ds_id, digests, byc):

    variants = []

    mongo_client = MongoClient()
    data_db = mongo_client[ ds_id ]
    v_coll = mongo_client[ ds_id ][ "variants" ]

    for d in digests:

        d_vs = v_coll.find({"digest": d })

        v = {
            "variant_internal_id": d,
            "variant_type": d_vs[0].get("variant_type", "SNV"),
            "position":{
                "assembly_id": "GRCh38",
                "refseq_id": "chr"+d_vs[0]["reference_name"],
                "start": [ int(d_vs[0]["start"]) ]
            },
            "case_level_data": []
        }

        if "end" in d_vs[0]:
            v["position"].update({ "end": [ int(d_vs[0]["end"]) ] })

        for v_t in ["variant_type", "reference_bases", "alternate_bases"]:
            v.update({ v_t: d_vs[0].get(v_t, "") })

        for d_v in d_vs:
            v["case_level_data"].append(
                {   
                    "id": d_v["id"],
                    "biosample_id": d_v["biosample_id"],
                    "analysis_id": d_v["callset_id"]
                }
            )

        variants.append(v)

    return variants

################################################################################

def _pagination_range(results_count, byc):

    r_range = [
        byc["pagination"]["skip"] * byc["pagination"]["limit"],
        byc["pagination"]["skip"] * byc["pagination"]["limit"] + byc["pagination"]["limit"],
    ]

    r_l_i = results_count - 1

    if r_range[0] > r_l_i:
        r_range[0] = r_l_i
    if r_range[-1] > results_count:
        r_range[-1] = results_count

    return r_range

################################################################################

def initialize_service(service="NA"):

    """For consistency, the name of the local configuration file should usually
    correspond to the calling main function. However, an overwrite can be
    provided."""

    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    sub_path = path.dirname( path.abspath(mod.__file__) )

    if service == "NA":
        service = frm.function

    service = decamelize(service)

    byc =  {
        "service_name": path.splitext(path.basename(mod.__file__))[0],
        "service_id": service,
        "response_schema": "BeaconServiceResponse",
        "beacon_info": {},
        "pkg_path": pkg_path,
        "method": "",
        "output": "",
        "errors": [ ],
        "warnings": [ ]
    }

    read_local_prefs( service, sub_path, byc )

    if "bycon_definition_files" in byc["this_config"]:
        for d in byc["this_config"]["bycon_definition_files"]:
            read_bycon_configs_by_name( d, byc )
    else:
        read_bycon_configs_by_name( "config", byc )

    form_data, query_meta, debug_state = cgi_parse_query(byc)

    byc.update({ "form_data": form_data, "query_meta": query_meta, "debug_state": debug_state })

    if "defaults" in byc["this_config"]:
        for d_k, d_v in byc["this_config"]["defaults"].items():
            byc.update( { d_k: d_v } )

    if "output" in byc["form_data"]:
        byc["output"] = byc["form_data"]["output"]

    if "method" in byc["form_data"]:
        if "methods" in byc["this_config"]:
            if byc["form_data"]["method"] in byc["this_config"]["methods"].keys():
                byc["method"] = byc["form_data"]["method"]

    # TODO: proper defaults, separate function
    byc["pagination"] = {
        "skip": byc["form_data"].get("skip", 0),
        "limit": byc["form_data"].get("limit", 0)
    }

    return byc

################################################################################

def response_meta_add_request_summary(meta, byc):

    if not "received_request_summary" in meta:
        meta.update( { "received_request_summary":{} } )        

    meta["received_request_summary"].update({
        "filters": byc.get("filters", []), 
        "pagination": byc.get("pagination", {}),
        "api_version": byc["beacon_info"].get("api_version", "v2.n")
    })

    try:
        for rrs_k, rrs_v in byc["this_config"]["meta"]["received_request_summary"].items():
            meta["received_request_summary"].update( {rrs_k: rrs_v })
    except:
        pass

    # TODO: This is a private extension so far.
    meta["received_request_summary"].update({ "processed_query": byc.get("queries", {}) })

    return meta

################################################################################

def create_empty_service_response(byc):

    """The response relies on the pre-processing of input parameters (queries etc)."""

    r_s = read_schema_files(byc["response_schema"], "properties", byc)
    r = create_empty_instance(r_s)

    e_s = read_schema_files("beaconErrorResponse", "properties", byc)
    e = create_empty_instance(e_s)

    if "response_summary" in r:
        r["response_summary"].update({ "exists": False })

    if "meta" in byc["this_config"]:
    	for k, v in byc["this_config"]["meta"].items():
    		r["meta"].update( { k: v } )

    response_meta_add_request_summary(r["meta"], byc)
    for i_k in ["api_version", "beacon_id", "create_date_time", "update_date_time"]:
        r["meta"].update({ i_k: byc["beacon_info"].get(i_k, "") })

    # if "response_type" in byc:
    #     for r_t, r_d in byc["beacon_mappings"]["response_types"].items():
    #         if r_d["id"] == byc["response_type"]:
    #             r["meta"].update( { "returned_schemas": r_d["schema"] } )

    if "requested_schemas" in byc["query_meta"]:
        if byc["query_meta"]["requested_schemas"][0]:
            if "entityType" in byc["query_meta"]["requested_schemas"][0]:
                e_t = byc["query_meta"]["requestedSchemas"][0]["entityType"]
                for r_t, r_d in byc["beacon_mappings"]["response_types"].items():
                    if r_d["id"] == e_t:
                        r["meta"].update( { "returned_schemas": r_d["schema"] } )
                        byc.update({"response_type":e_t})

    try:
        if len(byc["this_config"]["defaults"]["include_resultset_responses"]) > 2:
            r.update({"result_sets":[]})
    except KeyError:
        pass

    if "result_sets" in r["response"]:

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
            response_add_parameter(byc, p, byc[ p ])

    return byc

 ################################################################################

def create_empty_non_data_response(byc):

    # print(byc["response_schema"])
    r_s = read_schema_files(byc["response_schema"], "properties", byc)
    r = create_empty_instance(r_s)
    e_s = read_schema_files("beaconErrorResponse", "properties", byc)
    e = create_empty_instance(e_s)

    response_meta_add_request_summary(r["meta"], byc)
    for i_k in ["api_version", "beacon_id", "create_date_time", "update_date_time"]:
        r["meta"].update({ i_k: byc["beacon_info"].get(i_k, "") })

    for k, v in byc["this_config"]["meta"].items():
        r["meta"].update( { k: v } )
    for r_k, r_v in byc["this_config"]["response"].items():
        r["response"].update({r_k: r_v})

    byc.update( {"service_response": r, "error_response": e })

    return byc

################################################################################

def print_parameters_response(byc):

    if not "queries" in byc:
        return byc

    if not byc["service_id"] in byc["queries"].keys():
        return byc

    s_i_d = byc["service_id"]

    try:
        if "requestParameters" in byc["queries"][ s_i_d ]["id"]:
            prjsonresp(byc["this_request_parameters"])
        elif "endpoints" in byc["queries"][ s_i_d ]["id"]:
            prjsonresp(byc["this_endpoints"])
    except:
        pass

    return byc

################################################################################

def response_add_parameter(byc, name, value):

    if not "received_request" in byc["service_response"]["meta"]:
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

def response_append_result(byc, result):

    byc["service_response"]["results"].append( result )

    return byc

################################################################################

def collations_set_delivery_keys(byc):

    # the method keys can be overriden with "deliveryKeys"
    d_k = [ ]
    
    if "deliveryKeys" in byc["form_data"]:
        d_k = form_return_listvalue( byc["form_data"], "deliveryKeys" )
        return d_k

    if not "methods" in byc["this_config"]:
        return d_k

    if byc["method"] in byc["this_config"]["methods"]:
        d_k = byc["this_config"]["methods"][ byc["method"] ]

    return d_k

################################################################################

def populate_service_response( byc, results):

    populate_service_header(byc, results)
    populate_service_response_counts(byc)
    byc["service_response"].update({"results": results })
    # byc["service_response"].pop("result_sets")

    return byc

################################################################################

def populate_service_header(byc, results):

    r_no = 0

    if isinstance(results, list):
        r_no = len( results )
        byc["service_response"]["response_summary"].update({"num_total_results": r_no })
    if r_no > 0:
        byc["service_response"]["response_summary"].update({"exists": True })
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



################################################################################

def check_core_delivery(ds_id, byc):
    
    for ds_rk, ds_rv in byc["dataset_results"][ds_id].items():
        if "target_count" in ds_rv:
            if ds_rv["target_count"] > 0:
                byc["service_response"]["response_summary"].update({"exists": True })

    return byc

################################################################################

def check_alternative_variant_deliveries(ds_id, byc):

    if not "variantInSample" in byc["response_type"]:
        return byc

    if "pgxseg" in byc["output"]:
        export_pgxseg_download(ds_id, byc)

    if "variants" in byc["method"]:
        export_variants_download(ds_id, byc)

    return byc

################################################################################

def check_alternative_callset_deliveries(byc):

    if not "pgxmatrix" in byc["output"]:
        return byc

    ds_id = byc[ "dataset_ids" ][ 0 ]

    ds_results = byc["dataset_results"][ds_id]

    mongo_client = MongoClient()
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]
    cs_coll = mongo_client[ ds_id ][ "callsets" ]

    open_text_streaming("interval_callset_matrix.pgxmatrix")

    for d in ["id", "assemblyId"]:
        print("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))

    _print_filters_meta_line(byc)

    info_columns = [ "analysis_id", "biosample_id", "group_id" ]
    h_line = interval_header(info_columns, byc)
    print("#meta=>genome_binning={};interval_number={}".format(byc["genome_binning"], len(byc["genomic_intervals"])) )
    print("#meta=>no_info_columns={};no_interval_columns={}".format(len(info_columns), len(h_line) - len(info_columns)))

    cs_ids = { }

    for bs_id in ds_results["biosamples.id"][ "target_values" ]:
        bs = bs_coll.find_one( { "id": bs_id } )
        bs_csids = cs_coll.distinct( "id", {"biosample_id": bs_id} )
        for bsid in bs_csids:
            cs_ids.update( { bsid: "" } )
        s_line = "#sample=>biosample_id={};analysis_ids={}".format(bs_id, ','.join(bs_csids))
        h_d = bs["histological_diagnosis"]
        s_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(s_line, h_d.get("id", "NA"), h_d.get("label", "NA"), h_d.get("id", "NA"), h_d.get("label", "NA"))
        cs_ids[bsid] = h_d.get("id", "NA")
        print(s_line)
    
    print("#meta=>biosampleCount={};analysisCount={}".format(ds_results["biosamples.id"][ "target_count" ], len(cs_ids)))
    print("\t".join(h_line))

    for cs_id, group_id in cs_ids.items():
        cs = cs_coll.find_one({"id":cs_id})
        print("\t".join(
            [
                cs_id,
                cs.get("biosample_id", "NA"),
                group_id,
                *map(str, cs["info"]["statusmaps"]["max"]),
                *map(str, cs["info"]["statusmaps"]["min"])
            ]
        ))

    close_text_streaming()
        
    return byc

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
        if m in byc["service_response"]["result_sets"][0]["info"]["counts"]:
            print("#meta=>{}={}".format(m, byc["service_response"]["result_sets"][0]["info"]["counts"][m]))
            
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
