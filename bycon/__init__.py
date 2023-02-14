# __init__.py
import sys, inspect, glob
from os import pardir, path
from pathlib import Path

pkg_path = path.dirname( path.abspath(__file__) )
bycon_lib_path = path.join( pkg_path, "lib" )
sys.path.append( bycon_lib_path )

from aggregator_utils import *
from args_parsing import *
from cgi_parsing import *
from data_retrieval import *
from datatable_utils import *
from handover_generation import *
from interval_utils import *
from filter_parsing import *
from geomap_utils import *
from publication_utils import *
from query_execution import *
from query_generation import *
from read_specs import *
from response_remapping import *
from schema_parsing import *
from service_utils import *
from export_file_generation import *
from variant_parsing import *

c_f = Path( path.join( pkg_path, "config.yaml" ) )
config = load_yaml_empty_fallback( c_f )
conf_dir = path.join( pkg_path, "config")
byc = initialize_bycon(config)
d_f = Path( path.join( conf_dir, "beacon_defaults.yaml" ) )
byc.update({"beacon_defaults": load_yaml_empty_fallback( d_f ) })
defaults = byc["beacon_defaults"].get("defaults", {})
for d_k, d_v in defaults.items():
    byc.update( { d_k: d_v } )

read_bycon_definition_files(conf_dir, byc)
cgi_parse_query(byc)
