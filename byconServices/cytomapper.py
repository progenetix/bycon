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

    There is **currently only support for GRCh38**.

    #### Response Schema

    * <https://progenetix.org/services/schemas/CytobandMapping/>

    #### Parameters

    * `cytoBands` (path default)
        - a properly formatted cytoband annotation
        - "8", "9p11q21", "8q", "1p12qter"
    * or `chroBases`
        - `7:23028447-45000000`
        - `X:99202660`

    #### Examples (using the Progenetix resource as endpoint):

    * https://progenetix.org/services/cytomapper/8q21q24
    * https://progenetix.org/services/cytomapper/13q
    * https://progenetix.org/services/cytomapper?chroBases=12:10000000-45000000

    """
    cbr = Cytobands().cytobands_response()
    BeaconErrorResponse().respond_if_errors()
    print_json_response(ByconServiceResponse().populated_response([cbr]))
