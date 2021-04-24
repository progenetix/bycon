### Bycon - a Python-based environment for the Beacon v2 genomics API

#### More Information

Additional information may be available through [info.progenetix.org](https://info.progenetix.org/doc/bycon/byconplus.html).

##### Examples for v2 endpoints

**NOTE** The Beacon v2 endpoints are _currently_ implemented under
`https://progenetix.org/beacon/...`.

* `/filtering_terms`
  - <https://progenetix.org/beacon/filtering_terms/>
  - <https://progenetix.org/beacon/filtering_terms?filters=PMID>
  - <https://progenetix.org/beacon/filtering_terms?filters=NCIT,icdom>
  - <https://progenetix.org/beacon/filtering_terms?filters=NCIT,icdom,icdot&datasetIds=progenetix>
* `/biosamples/{id}`
  - <https://progenetix.org/beacon/biosamples/pgxbs-kftva5c8>
* `/biosamples/{id}/g_variants`
  - <https://progenetix.org/beacon/biosamples/pgxbs-kftva5c8/variants/>
  - **TBD**


```
{
  "meta": {
    "api_version": "2.0.0-draft.3",
    "beacon_id": "org.progenetix.beacon",
    "create_date_time": "2015-11-13",
    "info": "The main biosamples payload can be accessed in `response.results`.\n",
    "received_request": {
      "dataset": "progenetix",
      "dataset_ids": [
        "progenetix"
      ],
      "method": "details",
      "variant_pars": {
        "assemblyId": "GRCh38"
      }
    },
    "response_type": "BiosampleResponse",
    "returned_schemas": {
      "Biosample": "https://progenetix.org/services/schemas/Biosample/"
    },
    "update_date_time": "2021-03-23",
    "warnings": []
  },
  "response": {
    "beacon_handover": [],
    "error": {
      "error_code": 200,
      "error_message": ""
    },
    "exists": true,
    "info": {
      "counts": {
        "sampleCount": 1
      },
      "database_queries": {
        "biosamples": {
          "id": "pgxbs-kftva5c8"
        }
      }
    },
    "numTotalResults": 1,
    "results": [
      {
        "biocharacteristics": [
          {
            "id": "UBERON:0000029",
            "label": "lymph node"
          },
          {
            "id": "icdot-C77.9",
            "label": "Lymph nodes, NOS"
          },
          {
            "id": "icdom-96733",
            "label": "Mantle cell lymphoma"
          },
          {
            "id": "NCIT:C4337",
            "label": "Mantle Cell Lymphoma"
          }
        ],
        "description": "Mantle cell lymphoma",
        "external_references": [
          {
            "id": "geo:GSE13331",
            "label": null
          }
        ],
        "id": "pgxbs-kftva5c8",
        "info": {
          "callset_ids": [
            "pgxcs-kftvlegc"
          ],
          "cnvstatistics": {
            "cnvcoverage": 161672483,
            "cnvfraction": 0.056,
            "delcoverage": 119340049,
            "delfraction": 0.042,
            "dupcoverage": 42332434,
            "dupfraction": 0.015
          },
          "legacy_id": [
            "PGX_AM_BS_GSE13331_MCL98-13331"
          ]
        },
        "provenance": {
          "geo_location": {
            "geometry": {
              "coordinates": [
                -123.12,
                49.25
              ],
              "type": "Point"
            },
            "properties": {
              "ISO3166alpha3": "CAN",
              "city": "Vancouver",
              "country": "Canada",
              "label": "Vancouver, Canada",
              "latitude": 49.25,
              "longitude": -123.12,
              "precision": "city"
            },
            "type": "Feature"
          },
          "material": {
            "description": null,
            "id": "EFO:0009656",
            "label": "neoplastic sample"
          }
        }
      }
    ],
    "results_handover": [
      {
        "description": "create a CNV histogram from matched callsets",
        "handoverType": {
          "id": "pgx:handover:cnvhistogram",
          "label": "CNV Histogram"
        },
        "url": "https://progenetix.org/cgi-bin/PGX/cgi/samplePlots.cgi?method=cnvhistogram&;amp;accessid=30830aaa-27e9-45fc-becf-34e6f2e5a38f"
      },
      {
        "description": "retrieve data of the biosamples matched by the query",
        "handoverType": {
          "id": "pgx:handover:biosamples",
          "label": "Biosamples"
        },
        "url": "https://progenetix.org/beacon/biosamples?method=biosamples&;amp;accessid=f42df9bc-5d27-4afc-846a-5e49c734c7ab"
      },
      {
        "description": "Download all variants of matched samples - potentially huge dataset...",
        "handoverType": {
          "id": "pgx:handover:callsetsvariants",
          "label": "All Sample Variants (.json)"
        },
        "url": "https://progenetix.org/beacon/variants?method=callsetsvariants&;amp;accessid=f42df9bc-5d27-4afc-846a-5e49c734c7ab"
      },
      {
        "description": "Download all variants of matched samples - potentially huge dataset...",
        "handoverType": {
          "id": "pgx:handover:callsetspgxseg",
          "label": "All Sample Variants (.pgxseg)"
        },
        "url": "https://progenetix.org/beacon/variants?method=callsetspgxseg&;amp;accessid=f42df9bc-5d27-4afc-846a-5e49c734c7ab"
      }
    ]
  }
}
```
* `/g_variants?{query}`  
  - <https://progenetix.org/beacon/g_variants?requestType=variantRangeRequest&datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&start=20000000&end=22000000&filters=icdom-94403>
* `/g_variants/{id}`    
  - Since the _Progenetix_ framework treats all variant instances individually
  and an `id` parameter should be unique, variants are grouped as "equivalent"
  using the "digest" parameter. Remapping of the positional "id" argument to `digest`
  is handled internally.
  - <https://progenetix.org/beacon/g_variants/11:52900000-134452384:DEL?datasetIds=progenetix>
* `/g_variants/{id}/biosamples`
  - As above, but responding with the `biosamples` data.
  - <https://progenetix.org/beacon/g_variants/11:52900000-134452384:DEL/biosamples?datasetIds=progenetix>
  
##### Custom (yet)

* <https://beacon.progenetix.org/?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&variantType=DUP&filterLogic=AND&geneSymbol=MYC&varMinLength=1000000&varMaxLength=3000000&filters=icdom-80463>

* `/get-datasetids/`
  - dataset retrieval
  - <https://bycon.progenetix.org/get-datasetids/>
```
{
    "datasets": [
        { "id": "progenetix", "name": "progenetix" ...
```
* sample retrieval like "id" query by endpoint
  - This type of query emulates the endpoint based queries above through the parameters
    * `scope`
    * `id`
    * `response`
    Only providing `scope` or `response` without `id` will only work if other valid
    query parameters are provided.
  - <https://bycon.progenetix.org?id=PGX_AM_BS_GSM253289&datasetIds=progenetix&scope=biosamples>
  - <https://bycon.progenetix.org?id=PGX_AM_BS_GSM253289&datasetIds=progenetix&scope=biosamples&response=g_variants>
