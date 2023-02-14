#!/usr/bin/env python3

import sys
from os import path, environ, pardir
from copy import deepcopy
from liftover import get_lifter
from bycon import *

# local
# pkg_path = path.join( path.dirname( path.abspath(__file__) ), pardir, pardir )
# sys.path.append( pkg_path )

"""podmd

This app is used to prototype federated Beacon queries through
translating / sending / retrieving / converting Beacon queries in v2 format to
the format of the respective Beacon instances.

Queries are expected in the GRCh38 Beacon v2 format with parameters:

* `referenceName` as either `refseq:NC_...` or just `17` etc.
* `start`
* `alternateBases`
* `referenceBases` aren't supported by most olf beacons?

TODO:

* move from the "parameters per instance" to "parameters per version"
    - this may not work if those instances take "liberties" with their parameters ...
* split into different functions
    - a main aggregator which handles i/o for a list of beacons (i.e. the original)
    - an option to have it just return the query URLs w/o executing them, e.g. as handovers
    - a single query processor, taking the modified query url as input, retrieving the
      query & providing the response in the standard v2 format
* provide a prototype front-end which parses the list of transformed queries & uses
  the retriever to asynchronously populate the front-end, and to provide an aggregate
  summary
* message if query (e.g. brackets ...) is not supported
* liftover examples ... https://pypi.org/project/liftover/ 


#### Tests

* http://progenetix.org/beacon/aggregator/?requestedGranularity=boolean&referenceBases=G&alternateBases=A&limit=1000&skip=0&datasetIds=progenetix&assemblyId=GRCh38&referenceName=refseq%3ANC_000017.11&filterLogic=AND&includeDescendantTerms=True&start=7577120

* https://cancer.sanger.ac.uk/api/ga4gh/beacon?allele=A&chrom=7&dataset=cosmic&format=json&pos=140753336&ref=38
* http://progenetix.org/services/aggregator/debug=1
* http://progenetix.org/cgi/bycon/beaconServer/aggregator.py?debug=1&reference_name=7&start=140753335&alternate_bases=A&assemblyId=GRCh38&responseEntityId=genomicVariant
* http://progenetix.org/cgi/bycon/beaconServer/aggregator.py?assemblyId=GRCh38&referenceName=17&variantType=DEL&filterLogic=AND&start=7500000&start=7676592&end=7669607&end=7800000
"""

################################################################################
################################################################################
################################################################################

def main():

    aggregator()
   
################################################################################

def beaconAggregator():
    aggregator()

################################################################################

def aggregator():

    initialize_bycon_service(byc)
    parse_filters(byc)
    parse_variant_parameters(byc)
    generate_genomic_intervals(byc)
    create_empty_service_response(byc)    

    cgi_break_on_errors(byc)

    if "selected_beacons" in byc["form_data"]:
        byc["service_config"].update({"selected_beacons": byc["form_data"]["selected_beacons"]})

    b_p = byc["service_config"]["beacon_params"]["instances"]

    byc["service_response"]["meta"]["received_request_summary"]["requested_granularity"] ="boolean"
    check_switch_to_boolean_response(byc)
    byc["service_response"].update({"response": { "response_sets": [] }})

    for b in byc["service_config"]["selected_beacons"]:

        ext_defs = b_p[b]

        for ds_id in ext_defs.get("dataset_ids", [""]):

            byc["form_data"].update({"dataset_ids": [ds_id]})

            pvs = {}

            """
            Values (for the respective parameter names) are processed step-wise:
            1. defaults are read in
            2. form values w/ remap infor are processed
            3. the non-remapped p=v are added
            4. fixed `value` parameters are (over-)written
            TODO: should we be explicit in parsing selected parameters,
            i.e. evaluating all (relevant) v2 ones?
            """

            set_dataset_id(pvs, ext_defs, ds_id)
            set_default_values(pvs, ext_defs, byc)
            remap_parameters_values(pvs, ext_defs, byc)
            add_parameter_values(pvs, ext_defs, byc)
            remap_min_max_positions(pvs, ext_defs, byc)
            set_fixed_values(pvs, ext_defs, byc)

            url = "{}{}".format(ext_defs["base_url"], urllib.parse.urlencode(pvs))
            resp_start = time.time()
            r = retrieve_beacon_response(url, byc)
            resp_end = time.time()
            # prjsoncam(r)
            r_f = format_response(r, url, ext_defs, ds_id, byc)
            r_f["info"].update({"response_time": "{}ms".format(round((resp_end - resp_start) * 1000, 0)) })
            byc["service_response"]["response"]["response_sets"].append(r_f)

    for r in byc["service_response"]["response"]["response_sets"]:
        if r["exists"] is True:
            byc["service_response"]["response_summary"].update({"exists": True})
            continue

    cgi_print_response( byc, 200 )

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
