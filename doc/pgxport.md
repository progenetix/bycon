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
