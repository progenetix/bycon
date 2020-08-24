## _bycon_ Help

### `pgxport.py`

#### Options

* `-h`, `--help` 
    - this document
* `-j`, `--jsonqueries`
    - a JSON object with MongoDB query objects for one or more of the Progenetix
    schema data collections
    - in contrast to the native `mongo` environment, keywords have to be quoted
    (e.g. `"$regex"`)
    - please avoid to specify empty queries for aany of the collections

#### Examples

* search for all biosamples with a _cellosaurus_ identifier and mapped CNVs

```
pgxport.py -j '{
  "biosamples": {"external_references.type.id": {"$regex":"CVCL" } },
  "callsets": {"info.cnvstatistics.cnvfraction": {"$gt": 0} }
}'
```

* retrieve all Glioblastoma samples with a focal deletion CNV for the _CDKN2A_
locus on chromosome 9

```
pgxport.py -a 0.2 -j '{
        "biosamples": { "biocharacteristics.type.id": {"$regex":"icdom-94403" } },
        "variants": { "reference_name": "9", "variant_type": "DEL", "$and": [ {"start": { "$lt": 21975098 } }, {"start": { "$gt": 18000000 } } ], "$and": [ { "end": { "$gt": 21967753 } }, { "end": { "$lt": 26000000 } } ] }
}'
```

* The big one: retrieve all cancer coded samples from the default dataset
(arraymap) and perform default exports:


```
pgxport.py -a 0.1 -j '{
        "biosamples": { "biocharacteristics.type.id": {"$regex":"icdom-[98]" } },
}'

```

### `pgxupdate.py`

#### Options

* `-h`, `--help` 
    - this document
* `-f`
    - the input file containing the ICD-O and NCIt mappings
    - OpenOffice table; please see example for format of header etc.
    
#### Examples

```
bin/pgxupdate.py -f rsrc/progenetix-icdo-to-ncit.ods
```

### Lint

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
