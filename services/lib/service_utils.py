from os import path, pardir
import inspect
import json
from bson import json_util
import sys

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )
schema_path = path.join( pkg_path, "bycon" )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import cgi_parse_query,form_return_listvalue
from bycon.lib.read_specs import read_bycon_configs_by_name,read_local_prefs
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

def response_add_error(r, code, message):

    if not code:
        return r

    r["response"]["error"].update( { "error_code": code } )

    if message:
        r["response"]["error"].update( { "error_message": message } )

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
                s[ k ] = res[ k1 ][ k2 ]
            elif k in res.keys():
                if "start" in k or "end" in k:
                    s[ k ] = int(res[ k ])
                else:
                    s[ k ] = res[ k ]
        results.append( s )

    return results

################################################################################

def populate_service_response(r, results):

    if isinstance(results, list):
        r_no = len( results )
        r["response"]["info"].update({"count": r_no })
        if r_no > 0:
            r["response"].update({"exists": True })
    
    r["response"].update({"results": results })

    return r
