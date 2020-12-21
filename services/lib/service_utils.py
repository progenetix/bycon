from os import path, pardir
import sys

# local
lib_path = path.dirname( path.abspath(__file__) )
dir_path = path.join( lib_path, pardir )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )
from byconeer.lib.schemas_parser import *

################################################################################

def create_empty_service_response():

    r_s = read_schema_files("ServiceResponse", "properties", dir_path)
    r = create_empty_instance(r_s, dir_path)

    return r
