# __init__.py
import sys
from os import environ, path
from pathlib import Path

services_path = path.dirname( path.abspath(__file__) )
services_lib_path = path.join( services_path, "lib" )
sys.path.append( services_lib_path )

try:
    import bycon_bundler
    import bycon_plot
    import clustering_utils
    import collation_utils
    import cytoband_utils
    import datatable_utils
    import export_file_generation
    import file_utils
    import geomap_utils
    import interval_utils
    import service_helpers
    import service_response_generation
except Exception:
    if not "local" in ENV:
        print('Content-Type: text/plain')
        print('status: 302')
        print()
    print(traceback.format_exc())
    print()
    exit()
