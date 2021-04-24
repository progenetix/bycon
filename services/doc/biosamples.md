<!--podmd-->
## _biosamples_ Service

This endpoint is mostly aimed at providing _biosamples_ handover functionality. 
Since March 2021 the app represents a standard Beacon v2 endpoint and has been moved to the `/beacon/biosamples` path (still aliased unser `/services/biosamples`).

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

* <http://progenetix.org/beacon/biosamples?datasetIds=progenetix&assemblyId=GRCh38&includeDatasetResonses=ALL&requestType=null&referenceName=null&filterLogic=OR&filters=NCIT:C7376&filters=NCIT:C45665&filters=NCIT:C45655&filters=NCIT:C45655>
* <http://progenetix.org/beacon/biosamples?datasetIds=progenetix&filterLogic=OR&filters=NCIT:C7376,NCIT:C45665,NCIT:C45655,NCIT:C45655&method=ids>

<!--/podmd-->
