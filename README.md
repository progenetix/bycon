## A Python Based [Beacon API](https://beacon-project.io) Implementation for the [Progenetix](http://progenetix.org) Data Model

### Directory Structure

#### `bin`

* applications for data access & processing

#### `bycon`

* Python modules

#### `cgi`

* web server apps - "beacon" _et al._

#### `config`

* configuration files, separated for topic/scope
* YAML ...

#### `data/in`, `data/out`, `data/out/yaml`

* input and output for example and test data
* in `.gitignore`

#### `doc`

* documentation, in Markdown
* also invoked by `-h` flag

#### `rsrc`

* various resources beyond configuration data
    - mapping input table(s)
    - external schema dumps
    - ...

### Usage Examples

Below are some usage examples against the [Progenetix resources](http://progenetix.org).

* The standard Beacon+ CNV test call, retrieving samples with a focal deletion in the _CDKNA/B,MTAP_ locus in Glioblastomas
    - https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py?datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&startMin=18000000&startMax=21975097&endMin=21967753&endMax=26000000&referenceBases=N&filters=icdom-94403
* A pure filter call, getting the sample numbers for _NCIT:C3326_ (Adrenal Gland Pheochromocytoma):
    - https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py?assemblyId=GRCh38&datasetIds=arraymap,progenetix&filters=NCIT:C3326
* Service info for this Beacon:
    - https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py/service-info/
* A "classic" _BeaconAlleleRequest_, for brain stem gliomas with a particular mutation in the _EIF4A1_ gene:
    - https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py?datasetIds=dipg&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&start=7577120&referenceBases=G&alternateBases=A&filters=icdot-C71.7&
