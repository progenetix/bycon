## Bycon - a Python-based environment for the Beacon v2 genomics API

The `bycon` project - at least at its current stage - is a mix of _Progenetix_ (i.e. GA4GH object model derived, _MongoDB_ implemented) - data management, and the implementation of middleware & server for the Beacon API.

More information about the current status of the package can be found in the inline
documentation which is also [presented in an accessible format](https://info.progenetix.org/tags/Beacon.html) on the _Progenetix_
website.

### Directory Structure

##### `bin`

* applications for data access & processing

##### `bycon`

* Python modules for Beacon query and response functions

##### `pgy`

* Python modules for data management in the [MongoDB](http://mongodb.org) based
_Progenetix_ database environment

##### `config`

* configuration files, separated for topic/scope
* YAML ...

##### `data/in`, `data/out`, `data/out/yaml`

* input and output for example and test data
* in `.gitignore`

##### `doc`

* documentation, in Markdown
* also invoked by `-h` flag

##### `rsrc`

* various resources beyond configuration data
    - mapping input table(s)
    - external schema dumps
    - ...

#### Beacon+ v1 Examples

** standard test deletion CNV query
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
  - <https://bycon.progenetix.org/biosamples/PGX_AM_BS_HNSCC-GSF-an-10394?datasetIds=progenetix>
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
            "type" : { "id" : "icdot-C10.9", "label" : "Oropharynx" }
          },
          {
            "type" : { "id" : "icdom-80703", "label" : "Squamous cell carcinoma, NOS" }
          },
          {
            "type" : { "id" : "NCIT:C8181", "label" : "Oropharyngeal Squamous Cell Carcinoma" }
          }
        ],
        "geo_provenance" : {
          "label" : "Oberschleissheim, Germany",
          "precision" : "city",
          "city" : "Oberschleissheim",
          "country" : "Germany",
          "latitude" : 48.25,
          "longitude" : 11.56
        },
        ...
```
* `/biosamples/{id}/g_variants`
  - <https://bycon.progenetix.org/biosamples/PGX_AM_BS_HNSCC-GSF-an-10394/g_variants?datasetIds=progenetix>
* `/g_variants?{query}`  
  - <https://bycon.progenetix.org/g_variants?datasetIds=dipg&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=17&start=7572825&end=7579005&referenceBases=N&alternateBases=N>
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

* sample retrieval like "id" query by endpoint
  - This type of query emulates the endpoint based queries above through the parameters
    * `scope`
    * `id`
    * `response`
    Only providing `scope` or `response` without `id` will only work if other valid
    query parameters are provided.
  - <https://bycon.progenetix.org?id=PGX_AM_BS_GSM253289&datasetIds=arraymap&scope=biosamples>
  - <https://bycon.progenetix.org?id=PGX_AM_BS_GSM253289&datasetIds=arraymap&scope=biosamples&response=g_variants>


#### Some usage additional v1+ examples against the [Progenetix resources](http://progenetix.org)

* The standard Beacon+ CNV test call, retrieving samples with a focal deletion in the _CDKNA/B,MTAP_ locus in Glioblastomas
    - https://bycon.progenetix.org?datasetIds=arraymap,progenetix&assemblyId=GRCh38&includeDatasetResponses=ALL&referenceName=9&variantType=DEL&start=18000000&start=21975097&end=21967753&end=26000000&referenceBases=N&filters=icdom-94403
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

### Database Modifications

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
