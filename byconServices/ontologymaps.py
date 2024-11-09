from bycon import BYC, BeaconErrorResponse, print_json_response
from byconServiceLibs import ByconServiceResponse, OntologyMaps, read_service_prefs

def ontologymaps():
    """

    #### Examples
    
    * <https://progenetix.org/services/ontologymaps/?filters=NCIT:C3222>
    """
    results = OntologyMaps().ontology_maps_results()
    BeaconErrorResponse().respond_if_errors()
    ByconServiceResponse().print_populated_response(results)

