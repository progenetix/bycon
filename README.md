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

* https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py?datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&startMin=17999999&startMax=21975097&endMin=21967753&endMax=26000000&referenceBases=N&filters=icdom-94403
* https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py?assemblyId=GRCh38&datasetIds=arraymap,progenetix&filters=NCIT:C3326
* https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py?assemblyId=GRCh38&datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&startMin=17999999&startMax=21975097&endMin=21967753&endMax=26000000&referenceBases=N&filters=icdom-94403&filters=geolat%3A49%2Cgeolong%3A8.69%2Cgeodist%3A2000000&
* https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py
* https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py/service-info/
* https://progenetix.org/cgi-bin/bycon/cgi/byconplus.py?datasetIds=dipg&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&start=7577120&referenceBases=G&alternateBases=A&filters=icdot-C71.7&
