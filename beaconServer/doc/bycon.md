### Bycon - a Python-based environment for the Beacon genomics API

#### More Information

Additional information may be available through [info.progenetix.org](https://info.progenetix.org/doc/bycon/byconplus.html).

**NOTE** The Beacon v2 endpoints are _currently_ implemented under
`https://progenetix.org/beacon/...`. Documentation for Beacon v2 endpoints & use can be found through [[this link]](beacon_v2.md).

##### Examples

* standard test deletion CNV queries (these may take a minute or so...)
  - <https://bycon.progenetix.org/query?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&requestType=variantCNVrequest&referenceName=9&variantType=DEL&start=20000000&start=21975097&end=21967753&end=23000000&filters=icdom-94403>
  - <https://bycon.progenetix.org/query?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&requestType=variantCNVrequest&referenceName=9&variantType=DEL&start=18000000&start=21975097&end=21967753&end=26000000&filters=icdom-94403>
* retrieving biosamples w/ a given filter code
  - <https://bycon.progenetix.org/query?assemblyId=GRCh38&datasetIds=progenetix&filters=NCIT:C3326>
<!-- * beacon info (i.e. missing parameters return the info)
  - <https://bycon.progenetix.org>
 -->
* precise variant query together with filter
  - <https://bycon.progenetix.org/query?datasetIds=progenetix&assemblyId=GRCh38&requestType=variantAlleleRequest&start=7577120&referenceBases=G&alternateBases=A&filters=icdot-C71.7>
  
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
