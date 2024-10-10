from bycon import BYC, BeaconErrorResponse, print_json_response
from byconServiceLibs import ByconServiceResponse, OntologyMaps, read_service_prefs

"""podmd
* <https://progenetix.org/services/ontologymaps/?filters=NCIT:C3222>
podmd"""

def ontologymaps():
    OM = OntologyMaps()

    query = OM.ontology_maps_query()
    if len(query.keys()) < 1:
        BYC["ERRORS"].append("No correct filter value provided!")  
    results = OM.ontology_maps_results()
    BeaconErrorResponse().respond_if_errors()
    ByconServiceResponse().print_populated_response(results)

