#!/usr/local/bin/python3

import cgi, cgitb
import json, yaml
from os import path as path
from os import environ
import sys, os, datetime, argparse

# local
dir_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(path.abspath(dir_path), '..'))
from bycon import *

"""podmd

### Bycon - a Python-based environment for the Beacon v2 genomics API

##### Examples

* standard test deletion CNV query
  - <https://bycon.progenetix.org/query?datasetIds=arraymap&assemblyId=GRCh38&includeDatasetResponses=ALL&requestType=variantCNVrequest&referenceName=9&variantType=DEL&start=20000000&start=21975097&end=21967753&end=23000000&filters=icdom-94403>
  - <https://bycon.progenetix.org/query?datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&requestType=variantCNVrequest&referenceName=9&variantType=DEL&start=18000000&start=21975097&end=21967753&end=26000000&filters=icdom-94403>
* retrieving biosamples w/ a given filter code
  - <https://bycon.progenetix.org/query?assemblyId=GRCh38&datasetIds=arraymap,progenetix&filters=NCIT:C3326>
* beacon info (i.e. missing parameters return the info)
  - <https://bycon.progenetix.org>
* beacon info (i.e. specific request)
  - <https://bycon.progenetix.org/service-info/>
* precise variant query together with filter
  - <https://bycon.progenetix.org/query?datasetIds=dipg&assemblyId=GRCh38&requestType=variantAlleleRequest&start=7577120&referenceBases=G&alternateBases=A&filters=icdot-C71.7>

##### Examples for v2 endpoints

* `/filtering_terms`
  - <https://bycon.progenetix.org/filtering_terms/>
  - <https://bycon.progenetix.org/filtering_terms?prefixes=PMID>
  - <https://bycon.progenetix.org/filtering_terms?prefixes=NCIT,icdom>
  - <https://bycon.progenetix.org/filtering_terms?prefixes=NCIT,icdom,icdot&datasetIds=dipg>
* `/biosamples/{id}`
  - <https://bycon.progenetix.org/biosamples/PGX_AM_BS_HNSCC-GSF-an-10394?datasetIds=progenetix>
  - this will return an object `biosamples.{datasetid(s)}` where containing list(s) of
  the biosamples data objects (the multi-dataset approach seems strange here but
  in the case of progenetix & arraymap could in some cases make sense ...)

```
{
  "biosamples": {
    "progenetix": [
      {
        "id": "PGX_AM_BS_HNSCC-GSF-an-10394",
        "individual_id": "PGX_IND_HNSCC-GSF-an-10394",
        "age_at_collection": { "age": "P50Y" },
        "biocharacteristics": [
          {
            "type" : { "id" : "icdot-C10.9", "label" : "Oropharynx" }
          },
          {
            "type" : { "id" : "icdom-80703", "label" : "Squamous cell carcinoma, NOS" }
          },
          {
            "type" : { "id" : "NCIT:C8181", "label" : "Oropharyngeal Squamous Cell Carcinoma" }
          }
        ],
        "geo_provenance" : {
          "label" : "Oberschleissheim, Germany",
          "precision" : "city",
          "city" : "Oberschleissheim",
          "country" : "Germany",
          "latitude" : 48.25,
          "longitude" : 11.56
        },
        ...
```
* `/biosamples/{id}/g_variants`
  - <https://bycon.progenetix.org/biosamples/PGX_AM_BS_HNSCC-GSF-an-10394/g_variants?datasetIds=progenetix>
* `/g_variants?{query}`  
  - <https://beacon.progenetix.org/cgi/bycon/bin/byconplus.py/g_variants?requestType=variantRangeRequest&datasetIds=arraymap&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&start=20000000&end=22000000&filters=icdom-94403>
  - <https://bycon.progenetix.org/g_variants?datasetIds=arraymap&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&start=21500000&start=21975097&end=21967753&end=22500000&filters=icdom-94403>
* `/g_variants/{id}`    
  - Since the _Progenetix_ framework treats all variant instances individually
  and an `id` parameter should be unique, variants are grouped as "equivalent"
  using the "digest" parameter. Remapping of the positional "id" argument to `digest`
  is handled internally.
  - <https://bycon.progenetix.org/g_variants/DIPG_V_MAF_17_7577121_G_A?datasetIds=dipg>
* `/g_variants/{id}/biosamples`
  - As above, but responding with the `biosamples` data.
  - <https://bycon.progenetix.org/g_variants/DIPG_V_MAF_17_7577121_G_A/biosamples?datasetIds=dipg>
  
##### Custom (yet)

* sample retrieval like "id" query by endpoint
  - This type of query emulates the endpoint based queries above through the parameters
    * `scope`
    * `id`
    * `response`
    Only providing `scope` or `response` without `id` will only work if other valid
    query parameters are provided.
  - <https://bycon.progenetix.org?id=PGX_AM_BS_GSM253289&datasetIds=arraymap&scope=biosamples>
  - <https://bycon.progenetix.org?id=PGX_AM_BS_GSM253289&datasetIds=arraymap&scope=biosamples&response=g_variants>

podmd"""

################################################################################
################################################################################
################################################################################

def _get_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--filters", help="prefixed filter values, comma concatenated")
    parser.add_argument("-t", "--test", action='store_true', help="test from command line with default parameters")
    parser.add_argument("-i", "--info", action='store_true', help="test from command line for info")
    parser.add_argument("-n", "--filtering_terms", action='store_true', help="test filtering term response")
    args = parser.parse_args()

    return(args)

################################################################################

def main():

    byconplus()
    
################################################################################

def byconplus():
    
    with open( path.join( path.abspath( dir_path ), '..', "config", "defaults.yaml" ) ) as cf:
        config = yaml.load( cf , Loader=yaml.FullLoader)
    config[ "paths" ][ "module_root" ] = path.join( path.abspath( dir_path ), '..' )
    config[ "paths" ][ "out" ] = path.join( *config[ "paths" ][ "web_temp_dir_abs" ] )

    # input / definitions
    form_data = cgi_parse_query()
    args = _get_args()

    # TODO: "byc" becoming a proper object?!
    byc = {
        "config": config,
        "args": args,
        "form_data": form_data,
        "filter_defs": read_filter_definitions( **config[ "paths" ] ),
        "variant_defs": read_variant_definitions( **config[ "paths" ] ),
        "datasets_info": read_datasets_info( **config[ "paths" ] ),
        "service_info": read_service_info( **config[ "paths" ] ),
        "beacon_info": read_beacon_info( **config[ "paths" ] ),
        "beacon_paths": read_beacon_api_paths( **config[ "paths" ] ),
        "h->o": read_handover_info( **config[ "paths" ] ),
        "dbstats": dbstats_return_latest( **config ),
        "get_filters": False
    }

    byc["beacon_info"].update( { "datasets": update_datasets_from_dbstats(**byc) } )
    for par in byc[ "beacon_info" ]:
        byc[ "service_info" ][ par ] = byc[ "beacon_info" ][ par ]

    byc.update( { "endpoint": beacon_get_endpoint(**byc) } )
    byc.update( { "endpoint_pars": parse_endpoints( **byc ) } )
    byc.update( { "response_type": select_response_type( **byc ) } )

    byc.update( { "dataset_ids": select_dataset_ids( **byc ) } )
    byc.update( { "filters":  parse_filters( **byc ) } )

    respond_filtering_terms_request(**byc)
    respond_service_info_request(**byc)
    respond_empty_request(**byc)
    respond_get_datasetids_request(**byc)

    # adding arguments for querying / processing data
    byc.update( { "variant_pars": parse_variants( **byc ) } )
    byc.update( { "variant_request_type": get_variant_request_type( **byc ) } )
    # print(byc["variant_request_type"])
    byc.update( { "queries": beacon_create_queries( **byc ) } )
    # print(byc["queries"])

    # fallback - but maybe shouldbe an error response?
    if not byc[ "queries" ].keys():
        cgi_print_json_response(byc["service_info"])

    # TODO: There should be a better pplace for this ...
    if len(byc[ "dataset_ids" ]) < 1:
        cgi_exit_on_error("No `datasetIds` parameter provided.")

    # TODO: vove the response modification to somewhere sensible...
    dataset_responses = [ ]

    for ds_id in byc[ "dataset_ids" ]:

        byc.update( { "query_results": execute_bycon_queries( ds_id, **byc ) } )
        query_results_save_handovers( **byc )

        if byc["response_type"] == "return_biosamples":
            bios = handover_return_data( byc["query_results"]["bs._id"][ "id" ], **byc )
            dataset_responses.append( { ds_id: bios } )
        elif byc["response_type"] == "return_variants":
            vs = handover_return_data( byc["query_results"]["vs._id"][ "id" ], **byc )
            dataset_responses.append( { ds_id: vs } )
        else:
            dataset_responses.append( create_dataset_response( ds_id, **byc ) )   

    byc.update( { "dataset_responses": dataset_responses } )
    beacon_response = create_beacon_response(**byc)
    
    cgi_print_json_response(beacon_response)

################################################################################
################################################################################

if __name__ == '__main__':
    main()
