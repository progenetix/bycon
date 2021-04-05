from os import path, pardir
import inspect
import json
from pymongo import MongoClient
from bson import json_util
import sys

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )
schema_path = path.join( pkg_path, "bycon" )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import *
from bycon.lib.read_specs import read_bycon_configs_by_name,read_local_prefs
from bycon.lib.handover_generation import dataset_response_add_handovers
from byconeer.lib.schemas_parser import *

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

    byc =  {
        "service_name": path.splitext(path.basename(mod.__file__))[0],
        "pkg_path": pkg_path,
        "form_data": cgi_parse_query(),
        "these_prefs": read_local_prefs( service, sub_path ),
        "method": "",
        "errors": [ ],
        "warnings": [ ]
    }

    if "bycon_definition_files" in byc["these_prefs"]:
        for d in byc["these_prefs"]["bycon_definition_files"]:
            read_bycon_configs_by_name( d, byc )
    else:
        read_bycon_configs_by_name( "config", byc )

    if "defaults" in byc["these_prefs"]:
        for d_k, d_v in byc["these_prefs"]["defaults"].items():
            byc.update( { d_k: d_v } )

    if "method" in byc["form_data"]:
        m = byc["form_data"].getvalue("method")
        if "methods" in byc["these_prefs"]:
            if m in byc["these_prefs"]["methods"].keys():
                byc["method"] = m

    return byc

################################################################################

def create_empty_service_response(byc):

    r_s = read_schema_files("BeaconServiceResponse", "properties", schema_path)
    r = create_empty_instance(r_s)

    if "meta" in byc["these_prefs"]:
    	for k, v in byc["these_prefs"]["meta"].items():
    		r["meta"].update( { k: v } )

    if "beacon_info" in byc:
        try:
            for i_k in ["api_version", "beacon_id", "create_date_time", "update_date_time"]:
                r["meta"].update({ i_k: byc["beacon_info"][ i_k ] })
        except:
            pass

    if "errors" in byc:
        if len(byc["errors"]) > 0:
            response_add_error(r, 422, "::".join(byc["errors"]))

    if "queries" in byc:
        r["response"]["info"].update({ "database_queries": json.loads(json_util.dumps( byc["queries"] ) ) } )

    # saving the parameters to the response
    for p in ["method", "dataset_ids", "filters", "variant_pars"]:
        if p in byc:
            response_add_parameter(r, p, byc[ p ])

    return r

################################################################################

def response_add_parameter(r, name, value):

    if value:
        r["meta"]["received_request"].update( { name: value } )

    return r

################################################################################

def response_collect_errors(r, byc):

    # TODO: flexible list of errors
    if not byc[ "queries" ].keys():
      response_add_error(r, 422, "No (correct) query parameters were provided." )
    if len(byc[ "dataset_ids" ]) < 1:
      response_add_error(r, 422, "No `datasetIds` parameter provided." )
    if len(byc[ "dataset_ids" ]) > 1:
      response_add_error(r, 422, "More than 1 `datasetIds` value was provided." )
      
################################################################################

def response_add_error(r, code=200, message=""):

    r["response"]["error"].update( {
        "error_code": code,
        "error_message": message
    } )

    return r

################################################################################

def response_append_result(r, result):

    r["response"]["results"].append( result )

    return r

################################################################################

def response_set_delivery_keys(byc):

    # the method keys can be overriden with "deliveryKeys"
    d_k = [ ]
    if "deliveryKeys" in byc["form_data"]:
        d_k = form_return_listvalue( byc["form_data"], "deliveryKeys" )
    elif byc["method"] in byc["these_prefs"]["methods"]:
        d_k = byc["these_prefs"]["methods"][ byc["method"] ]

    return d_k

################################################################################

def response_map_results(data, byc):

    # the method keys can be overriden with "deliveryKeys"
    d_k = response_set_delivery_keys(byc)

    if len(d_k) < 1:
        return data

    results = [ ]

    for res in data:
        s = { }
        for k in d_k:
            # TODO: cleanup and add types in config ...
            if "." in k:
                k1, k2 = k.split('.')
                if k1 in res.keys():
                    if k2 in res[ k1 ]:
                        s[ k ] = res[ k1 ][ k2 ]
            elif k in res.keys():
                if "start" in k or "end" in k:
                    s[ k ] = int(res[ k ])
                else:
                    s[ k ] = res[ k ]
        results.append( s )

    return results

################################################################################

def populate_service_header(r, results):

    if isinstance(results, list):
        r_no = len( results )
        r["response"].update({"numTotalResults": r_no })
        if r_no > 0:
            r["response"].update({"exists": True })
            response_add_error(r, 200)

    return r

################################################################################

def populate_service_response_handovers(r, byc):

    if not "query_results" in byc:
        return r
    if not "dataset_ids" in byc:
        return r

    r["response"].update({ "results_handover": dataset_response_add_handovers(byc[ "dataset_ids" ][ 0 ], **byc) })

    return r

################################################################################

def populate_service_response_counts(r, byc):

    if not "query_results" in byc:
        return r
    if not "dataset_ids" in byc:
        return r

    counts = { }

    for c, c_d in byc["config"]["beacon_counts"].items():

        if c_d["h->o_key"] in byc["query_results"]:
            counts[ c ] = byc["query_results"][ c_d["h->o_key"] ]["target_count"]

    r["response"]["info"].update({ "counts": counts })

    return r


################################################################################


def populate_service_response( byc, r, results):

    populate_service_header(r, results)
    populate_service_response_handovers(r, byc)
    populate_service_response_counts(r, byc)
    r["response"].update({"results": results })

    return r

################################################################################

def create_pgxseg_header(ds_id, r, byc):

    p_h = []

    mongo_client = MongoClient()
    bs_coll = mongo_client[ ds_id ][ "biosamples" ]

    if not "pgxseg" in byc["method"]:
        return p_h

    for d in ["id", "assemblyId"]:
        p_h.append("#meta=>{}={}".format(d, byc["dataset_definitions"][ds_id][d]))
    for m in ["variant_count", "biosample_count"]:
        p_h.append("#meta=>{}={}".format(m, r["response"]["info"][m]))
    if "filters" in r["meta"]["received_request"]:
        p_h.append("#meta=>filters="+','.join(r["meta"]["received_request"]["filters"]))

    for bs_id in byc["query_results"]["bs.id"][ "target_values" ]:
        bs = bs_coll.find_one( { "id": bs_id } )
        h_line = "#sample=>sample_id={}".format(bs_id)
        for b_c in bs[ "biocharacteristics" ]:
            if "NCIT:C" in b_c["id"]:
                h_line = '{};group_id={};group_label={};NCIT::id={};NCIT::label={}'.format(h_line, b_c["id"], b_c["label"], b_c["id"], b_c["label"])
        p_h.append(h_line)
    p_h.append("{}\t{}\t{}\t{}\t{}\t{}".format("biosample_id", "reference_name", "start", "end", "log2", "variant_type" ) )

    return p_h

################################################################################

def print_variants_json(vs):

    l_i = len(vs) - 1
    for i,v in enumerate(vs):
        if i == l_i:
            print(json.dumps(v, indent=None, sort_keys=False, default=str, separators=(',', ':')), end = '')
        else:
            print(json.dumps(v, indent=None, sort_keys=False, default=str, separators=(',', ':')), end = ',')

################################################################################

def export_variants_download(vs, r, byc):

    populate_service_header(r, vs)
    open_json_streaming(r, "variants.json")
    print_variants_json(vs)
    close_json_streaming()

################################################################################

def print_variants_pgxseg(vs):

    for v in vs:
        if not "variant_type" in v:
            continue
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
        print("{}\t{}\t{}\t{}\t{}\t{}".format(v["biosample_id"], v["reference_name"], v["start"], v["end"], v["log2"], v["variant_type"]) )

################################################################################

def export_pgxseg_download(ds_id, r, vs, byc):

    p_h = create_pgxseg_header(ds_id, r, byc)

    open_text_streaming()
    for h_l in p_h:
        print(h_l)
    print_variants_pgxseg(vs)
    close_text_streaming()

################################################################################

