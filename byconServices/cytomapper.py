from bycon import (
    BeaconErrorResponse,
    BYC,
    Cytobands,
    print_json_response
)
from byconServiceLibs import ByconServiceResponse

def cytomapper():
    """
    The `cytomapper` function provides a JSON response with cytoband information
    such as matched cytobands and the genome coordinates of their extend.

    #### Examples (using the Progenetix resource as endpoint):

    * https://progenetix.org/services/cytomapper/8q21q24
    * https://progenetix.org/services/cytomapper/13q
    * https://progenetix.org/services/cytomapper?chroBases=12:10000000-45000000

    """
    cbr = Cytobands().cytobands_response()
    BeaconErrorResponse().respond_if_errors()
    print_json_response(ByconServiceResponse().populated_response([cbr]))
