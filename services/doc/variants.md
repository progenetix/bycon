<!--podmd-->
## _variants_ Service

This endpoint is mostly aimed at providing _variants_ handover functionality. 
However, the app uses the same query processing mechanism as the main _byconplus_
application.

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

* <https://progenetix.org/services/variants/?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus>
* <https://progenetix.test/services/variants/?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&variantType=DEL&filterLogic=AND&start=4999999&start=7676592&end=7669607&end=10000000&filters=cellosaurus&deliveryKeys=reference_name,start,end>

<!--/podmd-->

