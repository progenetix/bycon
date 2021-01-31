<!--podmd-->
## _biosamples_ Service

This endpoint is mostly aimed at providing _biosamples_ handover functionality. 
However, the app uses the same query processing mechanism as the main _byconplus_
application.

##### Methods
* ids:
	- id
* details:
	- id
	- description
	- biocharacteristics
	- external_references
	- provenance
	- info
* biocharacteristics:
	- id
	- description
	- biocharacteristics
* phenopackets:
	- id

##### Examples

* <http://progenetix.org/services/biosamples?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResonses=ALL&requestType=null&referenceName=null&filterLogic=OR&filters=NCIT:C7376&filters=NCIT:C45665&filters=NCIT:C45655&filters=NCIT:C45655>
* <http://progenetix.org/services/biosamples?datasetIds=progenetix&filterLogic=OR&filters=NCIT:C7376,NCIT:C45665,NCIT:C45655,NCIT:C45655&method=ids>


<!--/podmd-->
