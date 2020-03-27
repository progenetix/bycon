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
