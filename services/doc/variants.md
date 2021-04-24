<!--podmd-->
## _variants_ Service

This endpoint is mostly aimed at providing _variants_ handover functionality. 
Since March 2021 the app represents a standard Beacon v2 endpoint and has been
moved to the `/beacon/variants/` path (still aliased unser `/services/variants/`).

#### Methods

* `digests`:
  - digest
* `details`:
  - _id
  - biosample_id
  - callset_id
  - digest
  - reference_name
  - start
  - end
  - variant_type
  - reference_bases
  - alternate_bases
  - info

##### Examples

* <https://progenetix.org/beacon/variants/?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.test/beacon/variants/?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus&deliveryKeys=reference_name,start,end>

<!--/podmd-->

