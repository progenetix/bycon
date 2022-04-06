# __init__.py
from os import pardir, path
import sys, inspect

beacon_server_script_path = path.dirname( path.abspath(__file__) )
bycon_path = path.join( beacon_server_script_path, pardir )
bycon_lib_path = path.join( bycon_path, "lib" )
sys.path.append( bycon_lib_path )

from beacon_response_remaps import *
from cgi_parse import *
from datatable_utils import *
from handover_execution import *
from handover_generation import *
from interval_utils import *
from parse_filters import *
from parse_variants import *
from publication_utils import *
from query_execution import *
from query_generation import *
from read_specs import *
from remap_utils import *
from repository_utils import *
from schemas_parser import *
from service_utils import *
from variant_responses import *

byc = initialize_bycon()
c_f = Path( path.join( pkg_path, "config", "config.yaml" ) )
byc.update({"config": load_yaml_empty_fallback( c_f )})
cgi_parse_query(byc)
