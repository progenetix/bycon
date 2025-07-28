# __init__.py
import sys, traceback
from os import path

pkg_path = path.dirname( path.abspath(__file__) )
sys.path.append( pkg_path )

from config import *

bycon_lib_path = path.join( pkg_path, "lib" )
sys.path.append( bycon_lib_path )

# try block to give at least some feedback on errors
try:

    from beacon_auth import *
    from beacon_response_generation import *
    from bycon_helpers import *
    from bycon_info import *
    from bycon_summarizer import *
    from genome_utils import *
    from handover_generation import *
    from interval_utils import *
    from parameter_parsing import *
    from query_execution import *
    from query_generation import *
    from read_specs import *
    from response_remapping import *
    from schema_parsing import *
    from variant_mapping import *

    read_service_definition_files()
    update_rootpars_from_local_or_HOST()

    if (defaults := BYC["beacon_defaults"].get("defaults", {})):
        for d_k, d_v in defaults.items():
            BYC.update( { d_k: d_v } )

    ByconParameters().set_parameters()
    ByconEntities().set_entities()
    ByconDatasets().set_dataset_ids()

    # if (tm := BYC_PARS.get("test_mode")):
    BYC.update({"TEST_MODE": ByconH().truth(BYC_PARS.get("test_mode"))})

    set_user_name()
    set_returned_granularities()    

except Exception:
    if not "___shell___" in ENV:
        print('Content-Type: text/plain')
        print('status: 302')
        print()
    
    print(traceback.format_exc())
    print()
    exit()


