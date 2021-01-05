from os import path, pardir
import sys

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from byconeer.lib.schemas_parser import *

################################################################################

def create_empty_service_response(**these_prefs):

    r_s = read_schema_files("ServiceResponse", "properties", dir_path)
    r = create_empty_instance(r_s, dir_path)

    if "meta" in these_prefs:
    	for k, v in these_prefs["meta"].items():
    		r["meta"].update( { k: v } )

    return r
