## A Python Based [Beacon API](https://beacon-project.io) Implementation for the [Progenetix](http://progenetix.org) Data Model

The `bycon` project - at least at its current stage - is a mix of _Progenetix_ (i.e. GA4GH object model derived) - data structure management, and the implementation of middleware & server for the Beacon API.

While the current implementation runs nicely against the >100'000 samples / millions of genomic variants of the diverse Progenetix collections, it's not yet a drop-in Beacon implementation - unless you really know what you do.

More information about the current status of the package can be found in the inline
documentation which is also [presented in an accessible format](https://info.progenetix.org/tags/Beacon.html) on the _Progenetix_
website.

### Directory Structure

#### `bin`

* applications for data access & processing

#### `bycon`

* Python modules for Beacon query and response functions

#### `pgy`

* Python modules for data management in the [MogoDB](http://mongodb.org) based
_Progenetix_ database environment

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

#### Beacon

Below are some usage examples against the [Progenetix resources](http://progenetix.org).

* The standard Beacon+ CNV test call, retrieving samples with a focal deletion in the _CDKNA/B,MTAP_ locus in Glioblastomas
    - https://bycon.progenetix.org?datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&startMin=18000000&startMax=21975097&endMin=21967753&endMax=26000000&referenceBases=N&filters=icdom-94403
* A pure filter call, getting the sample numbers for _NCIT:C3326_ (Adrenal Gland Pheochromocytoma):
    - https://bycon.progenetix.org?assemblyId=GRCh38&datasetIds=arraymap,progenetix&filters=NCIT:C3326
* Service info for this Beacon:
    - https://bycon.progenetix.org/service-info/
* A "classic" _BeaconAlleleRequest_, for brain stem gliomas with a particular mutation in the _EIF4A1_ gene:
    - https://bycon.progenetix.org?datasetIds=dipg&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&start=7577120&referenceBases=G&alternateBases=A&filters=icdot-C71.7
* This is a range query for any SNV resulting in an **A** alternative allele, in a genomic range spanning the _EIF4A1_ gene:
    - https://bycon.progenetix.org?datasetIds=dipg&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&start=7572841&end=7578485&alternateBases=A&filters=icdot-C71.7
* Another range query, here looking if there are deletions affecting _TP53_ in pre-invasive breast cancer (DCIS, ICD-O 3 8500/2) in the [arraymap](http://arraymap.org) dataset:
    - https://bycon.progenetix.org?datasetIds=arraymap&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&start=7669608&end=7676593&variantType=DEL&filters=icdom-85002

#### Databases

* `bin/pgxport.py -d progenetix -a 0.5 -j '{ 
        "biosamples": { "biocharacteristics.type.id": {"$regex":"icdom-94403" } }}'`
    - uses the dataset `progenetix`
    - the provided _JSON_ query string for the _MongoDB_ backend will retrieve
    all samples from `progenetix.biosamples` which have an _ICD-O 3_ code of
    "9440/3" (pgx version is "icdom-94403") corresponding to a "Glioblastoma,
    NOS" diagnosis
    - unspecified output methods will use the current defaults
    - plot dots will have an opacity of "0.5"
    
* `bin/pgx_update_mappings.py -f rsrc/ICDOntologies.ods -d arraymap,progenetix`
    - updates NCIt mappings in the _arraymap_ and _progenetix_ databases
    from the specified mapping file (first table in file)
    - also fixes some prefixes to correct versions (e.g. `ncit` => `NCIT`)
* `bin/pgx_update_mappings.py -f rsrc/progenetix-icdo-to-ncit.ods -d arraymap,progenetix -y ~/switchdrive/work/GitHub/progenetix/ICDOntologies/current`
    - this version of the ICD => NCIT mapping updater will read from the
    specified input table and - besides updating the NCIt codes wich have
    different/missing values for the same ICD-O M+T combinations - write 
    the YAML files to the local Github repository for `ICDOntologies`
    (obviously YDMV)
