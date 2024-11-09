# __init__.py
import sys, traceback
from os import environ, path
from pathlib import Path

pkg_path = path.dirname( path.abspath(__file__) )
bycon_lib_path = path.join( pkg_path, "lib" )
sys.path.append( pkg_path )
sys.path.append( bycon_lib_path )

try:

    from config import *

    from beacon_auth import *
    from beacon_response_generation import *
    from bycon_helpers import *
    from cytoband_parsing import *
    from dataset_parsing import *
    from genome_utils import *
    from handover_generation import *
    from parameter_parsing import *
    from query_execution import *
    from query_generation import *
    from read_specs import *
    from response_remapping import *
    from schema_parsing import *
    from service_utils import *
    from variant_mapping import *

    # import byconServiceLibs

    read_service_definition_files()
    update_rootpars_from_local_or_HOST()
    rest_path_elements()
    set_beacon_defaults()
    arguments_set_defaults()
    parse_arguments()
    set_entities()
    initialize_bycon_service()
    parse_filters()

except Exception:
    if not "local" in ENV:
        print('Content-Type: text/plain')
        print('status: 302')
        print()
    
    print(traceback.format_exc())
    print()
    exit()
