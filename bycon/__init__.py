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

    from args_parsing import *
    from beacon_auth import *
    from beacon_response_generation import *
    from bycon_helpers import *
    from cgi_parsing import *
    from cytoband_parsing import *
    from dataset_parsing import *
    from genome_utils import *
    from handover_generation import *
    from parse_filters_request import *
    from query_execution import *
    from query_generation import *
    from read_specs import *
    from response_remapping import *
    from schema_parsing import *
    from service_utils import *
    from variant_mapping import *
    from parse_variant_request import *

    byc: object = {
        "parsed_config_paths": []
    }

    read_service_definition_files(byc)
    # updates `entity_defaults`, `dataset_definitions` and `local_paths`
    update_rootpars_from_local(LOC_PATH, byc)
    set_entity_mappings()
    set_beacon_defaults(byc)
    parse_arguments(byc)

except Exception:
    if not "local" in ENV:
        print('Content-Type: text/plain')
        print('status: 302')
        print()
    
    print(traceback.format_exc())
    print()
    exit()
