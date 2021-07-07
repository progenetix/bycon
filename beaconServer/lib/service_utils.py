from os import path, pardir
import inspect, json
from pymongo import MongoClient
from bson import json_util
from humps import camelize

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )

from cgi_utils import *
from handover_execution import handover_retrieve_from_query_results, handover_return_data
from handover_generation import dataset_response_add_handovers, query_results_save_handovers
from interval_utils import generate_genomic_intervals
from query_execution import execute_bycon_queries
from query_generation import  initialize_beacon_queries
from read_specs import read_bycon_configs_by_name,read_local_prefs
from schemas_parser import *
from variant_responses import normalize_variant_values_for_export

################################################################################

def run_beacon_init_stack(byc):

    parse_beacon_schema(byc)
    initialize_beacon_queries(byc)
    generate_genomic_intervals(byc)
    create_empty_service_response(byc)
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    return byc

################################################################################

def run_beacon(byc):

    # TODO
    if "results" in byc["service_response"]:
        byc["service_response"].pop("results")
    if "results_handover" in byc["service_response"]:
        byc["service_response"].pop("results_handover")

    if "BeaconCoreResponse" in byc["response_schema"]:
        for ds_id in byc["dataset_ids"]:
            execute_bycon_queries( ds_id, byc )
            check_core_delivery(ds_id, byc)
        return byc

    for r_set in byc["service_response"]["result_sets"]:

        ds_id = r_set["id"]

        if not "counts" in byc["service_response"]["info"]:
            byc["service_response"]["info"].update({"counts":{}})

        execute_bycon_queries( ds_id, byc )
        check_alternative_variant_deliveries(ds_id, byc)

        h_o, e = handover_retrieve_from_query_results(ds_id, byc)
        h_o_d, e = handover_return_data( h_o, e )
        if e:
            response_add_error(byc, 422, e )
        else:
            r_set.update({ "results_handovers": dataset_response_add_handovers(ds_id, byc) })

        for c, c_d in byc["config"]["beacon_counts"].items():
            if c_d["h->o_key"] in byc["dataset_results"][ds_id]:
                r_c = byc["dataset_results"][ds_id][ c_d["h->o_key"] ]["target_count"]
                r_set["info"]["counts"].update({ c: r_c })
                if c in byc["service_response"]["info"]["counts"]:
                    byc["service_response"]["info"]["counts"][c] += r_c
                else:
                    byc["service_response"]["info"]["counts"].update({c:r_c})

        if isinstance(h_o_d, list):
            r_no = len( h_o_d )
            r_set.update({"results_count": r_no })
            if r_no > 0:
                r_set.update({ "exists": True, "results": h_o_d })
                byc["service_response"]["response_summary"]["num_total_results"] += r_no

    if byc["service_response"]["response_summary"]["num_total_results"] > 0:
        byc["service_response"]["response_summary"].update({"exists": True })
        response_add_error(byc, 200)

    cgi_break_on_errors(byc)

    return byc

################################################################################

def initialize_service(service="NA"):

    """
    For consistency, the name of the local configuration file should usually
    correspond to the calling main function. However, an overwrite can be
    provided."""

    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    sub_path = path.dirname( path.abspath(mod.__file__) )

    if service == "NA":
        service = frm.function

    service = camel_to_snake(service)

    byc =  {
        "service_name": path.splitext(path.basename(mod.__file__))[0],
        "response_schema": "BeaconServiceResponse",
        "pkg_path": pkg_path,
        "these_prefs": read_local_prefs( service, sub_path ),
        "method": "",
        "output": "",
        "errors": [ ],
        "warnings": [ ]
    }

    if "bycon_definition_files" in byc["these_prefs"]:
        for d in byc["these_prefs"]["bycon_definition_files"]:
            read_bycon_configs_by_name( d, byc )
    else:
        read_bycon_configs_by_name( "config", byc )

    form_data, query_meta = cgi_parse_query(byc)
    byc.update({ "form_data": form_data, "query_meta": query_meta })

    if "defaults" in byc["these_prefs"]:
        for d_k, d_v in byc["these_prefs"]["defaults"].items():
            byc.update( { d_k: d_v } )

    if "output" in byc["form_data"]:
        byc["output"] = byc["form_data"]["output"]
 
    elif "method" in byc["form_data"]: # TODO: legacy
        if byc["form_data"]["method"] == "pgxseg" or byc["form_data"]["method"] == "pgxmatrix":
            byc["output"] = byc["form_data"]["method"]
            byc["form_data"].pop("method")

    if "method" in byc["form_data"]:
        if "methods" in byc["these_prefs"]:
            if byc["form_data"]["method"] in byc["these_prefs"]["methods"].keys():
                byc["method"] = byc["form_data"]["method"]

    return byc

################################################################################

def create_empty_service_response(byc):

    r_s = read_schema_files(byc["response_schema"], "properties", byc)
    r = create_empty_instance(r_s)
    e_s = read_schema_files("BeaconErrorResponse", "properties", byc)
    e = create_empty_instance(e_s)

    if "response_summary" in r:
        r["response_summary"].update({ "exists": False })

    if "meta" in byc["these_prefs"]:
    	for k, v in byc["these_prefs"]["meta"].items():
    		r["meta"].update( { k: v } )

    if "beacon_info" in byc:
        try:
            for i_k in ["api_version", "beacon_id", "create_date_time", "update_date_time"]:
                r["meta"].update({ i_k: byc["beacon_info"][ i_k ] })
        except:
            pass

    if "response_type" in byc:
        for r_t, r_d in byc["beacon_mappings"]["response_types"].items():
            if r_d["id"] == byc["response_type"]:
                r["meta"].update( { "returned_schemas": r_d["schema"] } )

    if "requested_schemas" in byc["query_meta"]:
        if byc["query_meta"]["requested_schemas"][0]:
            if "entityType" in byc["query_meta"]["requested_schemas"][0]:
                e_t = byc["query_meta"]["requestedSchemas"][0]["entityType"]
                for r_t, r_d in byc["beacon_mappings"]["response_types"].items():
                    if r_d["id"] == e_t:
                        r["meta"].update( { "returned_schemas": r_d["schema"] } )
                        byc.update({"response_type":e_t})


    if "result_sets" in r:

        r_set_s = read_schema_files("BeaconNonEmptyResultset", "properties", byc)
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
                r["result_sets"].append(ds_rset)

    byc.update( {"service_response": r, "error_response": e })

    # saving the parameters to the response
    for p in ["method", "dataset_ids", "filters", "variant_pars"]:
        if p in byc:
            response_add_parameter(byc, p, byc[ p ])

    if "errors" in byc:
        if len(byc["errors"]) > 0:
            response_add_error(byc, 422, "::".join(byc["errors"]))


    return byc

################################################################################

def response_add_parameter(byc, name, value):

    if not "received_request" in byc["service_response"]["meta"]:
        return byc

    if value:
        byc["service_response"]["meta"]["received_request"].update( { name: value } )

    return byc

################################################################################

def response_collect_errors(byc):

    # TODO: flexible list of errors
    if not byc[ "queries" ].keys():
      response_add_error(byc, 422, "No (correct) query parameters were provided." )
    # if len(byc[ "dataset_ids" ]) < 1:
    #   response_add_error(byc, 422, "No `datasetIds` parameter provided." )
    if len(byc[ "dataset_ids" ]) > 1:
      response_add_error(byc, 422, "More than 1 `datasetIds` value was provided." )
      
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
    elif byc["method"] in byc["these_prefs"]["methods"]:
        d_k = byc["these_prefs"]["methods"][ byc["method"] ]

    return d_k

################################################################################

def populate_service_response( byc, results):

    populate_service_header(byc, results)
    populate_service_response_handovers(byc)
    populate_service_response_counts(byc)
    byc["service_response"].update({"results": results })
    byc["service_response"].pop("result_sets")

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

def populate_service_response_handovers(byc):

    if not "dataset_results" in byc:
        return byc
    if not "dataset_ids" in byc:
        return byc

    # TODO: Needed? Switching to result_test?
    byc["service_response"].update({ "results_handover": dataset_response_add_handovers(byc[ "dataset_ids" ][ 0 ], byc) })

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
        for b_c in bs[ "biocharacteristics" ]:
            if "NCIT:C" in b_c["id"]:
                s_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(s_line, b_c["id"], b_c["label"], b_c["id"], b_c["label"])
                cs_ids[bsid] = b_c["id"]
        print(s_line)
    
    print("#meta=>biosampleCount={};analysisCount={}".format(ds_results["biosamples.id"][ "target_count" ], len(cs_ids)))
    print("\t".join(h_line))

    for cs_id, group_id in cs_ids.items():
        cs = cs_coll.find_one({"id":cs_id})
        f_line = [cs_id, cs["biosample_id"], group_id]
        for intv in cs["info"]["statusmaps"]["interval_values"]:
            f_line.append( str(intv["dupcoverage"]) )
        for intv in cs["info"]["statusmaps"]["interval_values"]:
            f_line.append( str(intv["delcoverage"]) )
        print("\t".join(f_line))

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
        for b_c in bs[ "biocharacteristics" ]:
            if "NCIT:C" in b_c["id"]:
                h_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(h_line, b_c["id"], b_c["label"], b_c["id"], b_c["label"])
        print(h_line)

    print("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format("biosample_id", "reference_name", "start", "end", "log2", "variant_type", "reference_bases", "alternate_bases" ) )

    return

################################################################################

def _print_filters_meta_line(byc):

    if "filters" in byc["service_response"]["meta"]["received_request"]:
        f_vs = []
        for f in byc["service_response"]["meta"]["received_request"]["filters"]:
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
