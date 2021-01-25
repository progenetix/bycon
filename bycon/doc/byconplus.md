### Bycon - a Python-based environment for the Beacon v2 genomics API

#### More Information

Additional information may be available through [info.progenetix.org](https://info.progenetix.org/doc/bycon/byconplus.html).

##### Examples

* standard test deletion CNV queries (these may take a minute or so...)
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
  - <https://bycon.progenetix.org/biosamples/pgxbs-kftva5c8?datasetIds=progenetix>
  - this will return an object `biosamples.{datasetid(s)}` where containing list(s) of
  the biosamples data objects (the multi-dataset approach seems strange here but
  in the case of progenetix & arraymap could in some cases make sense ...)

```
      {
        "id": "pgxbs-kftva5c8",
        "individual_id": "pgxind-kftx25h9",
        "description": "Mantle cell lymphoma",
        "sampledTissue": {
          "id": "UBERON:0000029",
          "label": "lymph node"
        },
        "biocharacteristics": [
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
        "individual_age_at_collection": "P42Y",
        "data_use_conditions": {
          "id": "DUO:0000004",
          "label": "no restriction"
        },
        "external_references": [
          {
            "id": "geo:GSE13331"
          }
        ],
        "info": {
          "callset_ids": [
            "pgxcs-kftvlegc"
          ],
          "cnvstatistics": {
            "cnvfraction": 0.053,
            "delfraction": 0.039,
            "dupfraction": 0.014
          },
          "legacy_id": "PGX_AM_BS_GSE13331_MCL98-13331"
        },
        "provenance": {
          "geo_location": {
            "type: "Feature",
            "properties": {
              "ISO3166alpha3": "CAN",
              "city": "Vancouver",
              "country": "Canada",
              "label": "Vancouver, Canada",
              "latitude": 49.25,
              "longitude": -123.12,
              "precision": "city"
            },
            "geometry": {
              "coordinates": [
                -123.12,
                49.25
              ],
              "type": "Point"
            },
          },
          "material": {
            "id": "EFO:0009656",
            "label": "neoplastic sample"
          }
        },
        "updated": "2020-09-10 17:44:04.887000"
      }
```
* `/biosamples/{id}/g_variants`
  - <https://bycon.progenetix.org/biosamples/pgxbs-kftva5c8/g_variants?datasetIds=progenetix>
* `/g_variants?{query}`  
  - <https://bycon.progenetix.org/g_variants?requestType=variantRangeRequest&datasetIds=arraymap&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&start=20000000&end=22000000&filters=icdom-94403>
* `/g_variants/{id}`    
  - Since the _Progenetix_ framework treats all variant instances individually
  and an `id` parameter should be unique, variants are grouped as "equivalent"
  using the "digest" parameter. Remapping of the positional "id" argument to `digest`
  is handled internally.
  - <https://bycon.progenetix.org/g_variants/11:52900000-134452384:DEL?datasetIds=progenetix>
* `/g_variants/{id}/biosamples`
  - As above, but responding with the `biosamples` data.
  - <https://bycon.progenetix.org/g_variants/11:52900000-134452384:DEL/biosamples?datasetIds=progenetix>
  
##### Custom (yet)

* `/get-datasetids/`
  - dataset retrieval
  - <https://bycon.progenetix.org/get-datasetids/>
```
{
    "datasets": [
        { "id": "arraymap", "name": "arraymap" },
        { "id": "progenetix", "name": "progenetix" ...
```
* sample retrieval like "id" query by endpoint
  - This type of query emulates the endpoint based queries above through the parameters
    * `scope`
    * `id`
    * `response`
    Only providing `scope` or `response` without `id` will only work if other valid
    query parameters are provided.
  - <https://bycon.progenetix.org?id=PGX_AM_BS_GSM253289&datasetIds=arraymap&scope=biosamples>
  - <https://bycon.progenetix.org?id=PGX_AM_BS_GSM253289&datasetIds=arraymap&scope=biosamples&response=g_variants>
