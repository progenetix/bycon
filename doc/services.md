## Bycon _services_

The _bycon_ environment provides a number of data services which make use of
resources in the _Progenetix_ environment.

#### _collations_

* provides access to information about data "subsets" in the Progenetix project
databases
  - typically aggregations of samples sharing an ontology code (e.g. NCIT) or 
  external identifier (e.g. PMID)

##### Examples

* <https://progenetix.org/services/collations?filters=NCIT>
* <http://progenetix.org/cgi-bin/bycon/bin/collations.py?filters=NCIT&datasetIds=progenetix&method=counts>
* <http://progenetix.org/services/collations?filters=PMID&datasetIds=progenetix&method=counts&callback=4445-9938-cbat-9891-kllt>


#### _publications_

* provides access to information about data "subsets" in the Progenetix project
databases
  - typically aggregations of samples sharing an ontology code (e.g. NCIT) or 
  external identifier (e.g. PMID)

##### Examples

* <http://progenetix.org/cgi/bycon/bin/publications.py?debug=1&filters=PMID,genomes:&gt;200,arraymap:&gt;1&method=counts>
* <http://progenetix.org/cgi/bycon/bin/publications.py?filters=PMID:22824167&filterPrecision=exact&method=details>

#### _cytomapper_

* provides mappings from genome coordinates to cytobands an vice versa
* can be used e.g in Beacon interface implementations, to facilitate the input
of genome coordinates
* requires either
  * a properly formatted cytoband annotation (`cytoBands`)
    - "8", "9p11q21", "8q", "1p12qter"
  * or a concatenated `chroBases` parameter
    - `7:23028447-45000000`
    - `X:99202660`
* a different `assemblyId` then the assumed _GRCh38_ default can be provided


##### Examples

* <https://progenetix.org/services/cytomapper?assemblyId=NCBI36.1&cytoBands=8q>
* <https://progenetix.org/services/cytomapper?cytoBands=8q21q24.1&assemblyId=hg18>
* <https://progenetix.org/services/cytomapper?chroBases=17:800000-24326000>

#### _genespans_

* genomic mappings of gene coordinats
* initially limited to _GRCh38_ and overall CDS extension
* responds to (start-anchored) text input of HUGO gene symbols using the `geneId`
parameter
* returns a list of matching gene objects (see below under __Response Formats__)

##### Examples

* <https://progenetix.org/services/genespans?geneId=CDKN2>

### URL Mapping

The service URL format `progenetix.org/services/__service-name__?parameter=value`
is a shorthand for `progenetix.org/cgi-bin/bycon/bin/__service-name__.py?parameter=value`.

The `services` application deparses a request URI and calls the respective
script. The functionality is combined with the correct configuration of a 
rewrite in the server configuration:

```
RewriteRule     "^/services(.*)"     /cgi-bin/bycon/bin/services.py$1      [PT]
```

### Callback handling

The JSON response (see below) will be wrapped in a callback function if a `callback` 
parameter is provided e.g. for Ajax functionality.

* <http://progenetix.org/services/collations?filters=PMID&datasetIds=progenetix&method=counts&callback=4445-9938-cbat-9891-kllt>

### Response formats

Standard responses are provided as `Content-Type: application/json`. The wrapper
format, as defined in the cofigurartion (`config/config.yaml`) provides a `data`
root parameter:

```
response_object_schema:
  parameters: { }
  data: { }
  errors: [ ]
  warnings: [ ]
```

This (incomplete) example response may help with understanding the general
format. Here, the data is a dictionary/object with a single key (`genes`):

##### Request  Example

* <https://progenetix.org/services/genespans?geneId=CDKN2>

##### Response Example

```
{
    "parameters": {
        "assemblyId": "GRCh38",
        "geneId": "CDKN2A"
    },
    "data": {
        "genes": [
            {
                "cds_end_max": 21994330,
                "cds_start_min": 21968228,
                "gene_entrez_id": 1029,
                "gene_symbol": "CDKN2A",
                "reference_name": "9"
            },
            {
                "cds_end_max": 183447426,
                "cds_start_min": 183444797,
                "gene_entrez_id": 55602,
                "gene_symbol": "CDKN2AIP",
                "reference_name": "4"
            },
            {
                "cds_end_max": 134411853,
                "cds_start_min": 134402914,
                "gene_entrez_id": 91368,
                "gene_symbol": "CDKN2AIPNL",
                "reference_name": "5"
            }
        ]
    },
    "errors": [],
    "warnings": []
}
```
