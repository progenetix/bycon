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
  - <https://bycon.progenetix.org/biosamples/pgxbs-kftva59y?datasetIds=progenetix>
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
            "type": {
              "id": "icdot-C71.6",
              "label": "cerebellum"
            }
          },
          {
            "type": {
              "id": "icdom-94703",
              "label": "Medulloblastoma, NOS"
            }
          },
          {
            "type": {
              "id": "NCIT:C3222",
              "label": "Medulloblastoma"
            }
          }
        ],
        "data_use_conditions": {
          "id": "DUO:0000004",
          "label": "no restriction"
        },
        "provenance": {
          "geo": {
            "ISO-3166-alpha3": "TUR",
            "city": "Antalya",
            "country": "Turkey",
            "geojson": {
              "coordinates": [
                30.7,
                36.91
              ],
              "type": "Point"
            },
            "label": "Antalya, Turkey",
            "latitude": 36.91,
            "longitude": 30.7,
            "precision": "city"
          },
          "material": {
            "type": {
              "id": "EFO:0009656",
              "label": "neoplastic sample"
            }
          }
        },
        "sampledTissue": {
          "id": "UBERON:0002037",
          "label": "cerebellum"
        },
        ...
```
* `/biosamples/{id}/g_variants`
  - <https://bycon.progenetix.org/biosamples/PGX_AM_BS_HNSCC-GSF-an-10394/g_variants?datasetIds=progenetix>
* `/g_variants?{query}`  
  - <https://beacon.progenetix.org/cgi/bycon/bycon/byconplus.py/g_variants?requestType=variantRangeRequest&datasetIds=arraymap&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&start=20000000&end=22000000&filters=icdom-94403>
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
