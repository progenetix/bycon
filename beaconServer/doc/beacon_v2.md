### Bycon - a Python-based environment for the Beacon v2 genomics API

#### More Information

Additional information may be available through [info.progenetix.org](https://info.progenetix.org/doc/bycon/byconplus.html).

**NOTE** The Beacon v2 endpoints are _currently_ implemented under
`https://progenetix.org/beacon/...`.

## Progenetix & Beacon<span style="color: red; font-weight: 800;">+</span>

The Beacon+ implementation - developed in the Python & MongoDB based [`bycon` project](https://github.com/progenetix/bycon/) -
implements an expanding set of Beacon v2 paths for the [Progenetix](http://progenetix.org)
resource.

### Examples

#### Base `/filtering_terms`

##### `/filtering_terms/`

* [/filtering_terms/](https://progenetix.org/beacon/filtering_terms/)


##### `/filtering_terms/` + query

* [/filtering_terms/?filters=PMID](https://progenetix.org/beacon/filtering_terms/?filters=PMID)
* [/filtering_terms/?filters=NCIT,icdom](https://progenetix.org/beacon/filtering_terms/?filters=NCIT,icdom)

----

#### Base `/biosamples`

##### `/biosamples/` + query

* [/biosamples/?filters=cellosaurus:CVCL_0004](https://progenetix.org/beacon/biosamples/?filters=cellosaurus:CVCL_0004)
  - this example retrieves all biosamples having an annotation for the Cellosaurus _CVCL_0004_
  identifier (K562)

##### `/biosamples/{id}/`

* [/biosamples/pgxbs-kftva5c9/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/)
  - retrieval of a single biosample

##### `/biosamples/{id}/variants/` & `/biosamples/{id}/variants_in_sample/`

* [/biosamples/pgxbs-kftva5c9/variants/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/variants/)
* [/biosamples/pgxbs-kftva5c9/variants/](http://progenetix.org/beacon/biosamples/pgxbs-kftva5c9/variants_in_sample/)
  - retrieval of all variants from a single biosample
  - currently - and especially since for a mostly CNV containing resource - `variants` means "variant instances" (or as in the early v2 draft `variantsInSample`)

----

#### Base `/individuals`

##### `/individuals/` + query

* [/individuals/?filters=NCIT:C7541](https://progenetix.org/beacon/individuals/?filters=NCIT:C7541)
  - this example retrieves all individuals having an annotation associated with _NCIT:C7541_ (retinoblastoma)
  - in Progenetix, this particular code will be part of the annotation for the _biosample(s)_ associated with the returned individual
* [/individuals/?filters=PATO:0020001,NCIT:C9291](https://progenetix.org/beacon/individuals/?filters=PATO:0020001,NCIT:C9291)
  - this query returns information about individuals with an anal carcinoma (**NCIT:C9291**) and a known male genotypic sex (**PATO:0020001**)
  - in Progenetix, the information about its sex is associated with the _Individual_ object (and rtherefore in the _individuals_ collection), whereas the information about the cancer type is a property of the _Biosample_ (and therefore stored in the _biosamples_ collection)

##### `/individuals/{id}/`

* [/biosamples/pgxind-kftx25hb/](http://progenetix.org/beacon/biosamples/pgxind-kftx25hb/)
  - retrieval of a single individual

##### `/individuals/{id}/variants/` & `/individuals/{id}/variants_in_sample/`

* [/individuals/pgxind-kftx25hb/variants/](http://progenetix.org/beacon/individuals/pgxind-kftx25hb/variants/)
* [/individuals/pgxind-kftx25hb/variants/](http://progenetix.org/beacon/individuals/pgxind-kftx25hb/variants_in_sample/)
  - retrieval of all variants from a single individual
  - currently - and especially since for a mostly CNV containing resource - `variants` means "variant instances" (or as in the early v2 draft `variantsInSample`) 

----

#### Base `/variants`

There is currently (April 2021) still some discussion about the implementation and naming
of the different types of genomic variant endpoints. Since the Progenetix collections
follow a "variant observations" principle all variant requests are directed against
the local `variants` collection.

If using `g_variants` or `variants_in_sample`, those will be treated as aliases.

##### `/variants/` + query

* [/variants/?assemblyId=GRCh38&referenceName=17&variantType=DEL&filterLogic=AND&start=7500000&start=7676592&end=7669607&end=7800000](http://progenetix.org/beacon/variants/?assemblyId=GRCh38&referenceName=17&variantType=DEL&filterLogic=AND&start=7500000&start=7676592&end=7669607&end=7800000)
  - This is an example for a Beacon "Bracket Query" which will return focal deletions in the TP53 locus (by position).

##### `/variants/{id}/` or `/variants_in_sample/{id}` or `/g_variants/{id}/`

* [/variants/5f5a35586b8c1d6d377b77f6/](http://progenetix.org/beacon/variants/5f5a35586b8c1d6d377b77f6/)
* [/variants_in_sample/5f5a35586b8c1d6d377b77f6/](http://progenetix.org/beacon/variants_in_sample/5f5a35586b8c1d6d377b77f6/)

##### `/variants/{id}/biosamples/` & `variants_in_sample/{id}/biosamples/`

* [/variants/5f5a35586b8c1d6d377b77f6/biosamples/](http://progenetix.org/beacon/variants/5f5a35586b8c1d6d377b77f6/biosamples/)
* [/variants_in_sample/5f5a35586b8c1d6d377b77f6/biosamples/](http://progenetix.org/beacon/variants_in_sample/5f5a35586b8c1d6d377b77f6/biosamples/)


--------------------------------------------------------------------------------

### Structure of the 

(Subject to change ...)

```
{
  "meta": {
    "api_version": "2.0.0-draft.3",
    "beacon_id": "org.progenetix.beacon",
    "create_date_time": "2015-11-13",
    "info": "The main biosamples payload can be accessed in `results`.\n",
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
    "response_type": "biosample",
    "returned_schemas": {
      "Biosample": "https://progenetix.org/services/schemas/biosample/"
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
    "num_total_results": 1,
    "result_sets": [
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
    ],
    "results_handover": [
      {
        "description": "create a CNV histogram from matched callsets",
        "handoverType": {
          "id": "pgx:handover:cnvhistogram",
          "label": "CNV Histogram"
        },
        "url": "https://progenetix.org/cgi-bin/PGX/cgi/samplePlots.cgi?output=cnvhistogram&;amp;accessid=30830aaa-27e9-45fc-becf-34e6f2e5a38f"
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
        "url": "https://progenetix.org/beacon/variants?output=callsetsvariants&;amp;accessid=f42df9bc-5d27-4afc-846a-5e49c734c7ab"
      },
      {
        "description": "Download all variants of matched samples - potentially huge dataset...",
        "handoverType": {
          "id": "pgx:handover:callsetspgxseg",
          "label": "All Sample Variants (.pgxseg)"
        },
        "url": "https://progenetix.org/beacon/variants?output=callsetspgxseg&;amp;accessid=f42df9bc-5d27-4afc-846a-5e49c734c7ab"
      }
    ]
  }
}
```
  
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
