import re, yaml
import json
from os import path as path
  
################################################################################

def read_beacon_v2_spec(**kwargs):

    # TODO: proper integration with path from config etc.
    beacon_defs = {}
    with open( path.join(path.abspath(kwargs[ "config" ][ "paths" ][ "module_root" ]), "rsrc", "specification-v2", "beacon.yaml") ) as bspec:
        beacon_defs = yaml.load( bspec , Loader=yaml.FullLoader)

    print("[")
    print(json.dumps(beacon_defs["components"]["schemas"].keys(), indent=4, sort_keys=True, default=str))
    print(",")
    print(json.dumps(beacon_defs["components"]["schemas"]["ResponseBasicStructure"][ "properties" ].keys(), indent=4, sort_keys=True, default=str))
    print(",")
    print(json.dumps(beacon_defs["components"]["schemas"]["BeaconDatasetAlleleResponse"][ "properties" ].keys(), indent=4, sort_keys=True, default=str))
    print("]")
    exit()
    return( beacon_defs )

################################################################################
