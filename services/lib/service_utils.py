from os import path, pardir
import sys

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from bycon.lib.cgi_utils import cgi_parse_query
from bycon.lib.read_specs import read_bycon_configs_by_name,read_local_prefs
from byconeer.lib.schemas_parser import *

################################################################################

def initialize_service(service):

    byc =  {
        "pkg_path": pkg_path,
        "form_data": cgi_parse_query(),
        "config": read_bycon_configs_by_name("config"),
        "these_prefs": read_local_prefs( service, dir_path ),
        "method": "",
        "errors": [ ],
        "warnings": [ ]
    }

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

def create_empty_service_response(**byc):

    r_s = read_schema_files("ServiceResponse", "properties", dir_path)
    r = create_empty_instance(r_s, dir_path)

    if "meta" in byc["these_prefs"]:
    	for k, v in byc["these_prefs"]["meta"].items():
    		r["meta"].update( { k: v } )

    return r

################################################################################

def populate_service_response(r, results):

    if isinstance(results, list):
        r_no = len( results )
        r["response"]["info"].update({"count": r_no })
        if r_no > 0:
            r["response"].update({"exists": True })
    
    r["response"].update({"results": results })

    return r
