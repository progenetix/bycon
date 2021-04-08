#!/usr/local/bin/python3

import cgi, cgitb, sys
from os import path, pardir

# local
dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, pardir )
sys.path.append( pkg_path )

from bycon import *

"""podmd
* <https://progenetix.org/cgi/bycon/services/individuals.py?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.org/beacon/individuals?datasetIds=progenetix&filters=cellosaurus:CVCL_0030>
podmd"""

################################################################################
################################################################################
################################################################################

def main():

    individuals()
    
################################################################################

def individuals():

    byc = initialize_service()
    parse_beacon_schema(byc)

    select_dataset_ids(byc)
    check_dataset_ids(byc)

    get_filter_flags(byc)
    parse_filters(byc)

    # adding arguments for querying / processing data
    parse_variants(byc)
    get_variant_request_type(byc)
    generate_queries(byc)

    create_empty_service_response(byc)
    response_collect_errors(byc)
    cgi_break_on_errors(byc)

    ds_id = byc[ "dataset_ids" ][ 0 ]
    response_add_parameter(byc, "dataset", ds_id )

    execute_bycon_queries( ds_id, byc )
    query_results_save_handovers(byc)

    access_id = byc["query_results"][ byc["h->o_access_key"] ][ "id" ]

    h_o, e = retrieve_handover( access_id, **byc )
    h_o_d, e = handover_return_data( h_o, e )
    if e:
        response_add_error(byc, 422, e )

    cgi_break_on_errors(byc)

    populate_service_response( byc, response_map_results(h_o_d, byc))

    cgi_print_json_response( byc, 200 )

################################################################################
################################################################################

if __name__ == '__main__':
    main()
