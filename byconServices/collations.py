from bycon import print_json_response
from byconServiceLibs import ByconServiceResponse

def collations():
    ByconServiceResponse().print_collations_response()
